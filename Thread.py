import time
import os
import socket
from datetime import datetime
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
from pymodbus.exceptions import ModbusException as ModEx


base_dir = os.path.dirname(__file__)


class ReadSignals(QObject):
    result_temp = pyqtSignal(int, str, list)
    result_log = pyqtSignal(object)
    result_log_connect = pyqtSignal(object)
    connect_check = pyqtSignal(int, bool)
    connect_data = pyqtSignal(int)
    lucky_attemp = pyqtSignal(int, bool)
    check_cell = pyqtSignal(int, bool)
    error_read = pyqtSignal(object)
    error_modbus = pyqtSignal(object)


class LogWriter(QRunnable):
    def __init__(self, mode, obj_name, msg):
        super(LogWriter, self).__init__()
        try:
            if mode == 'info':
                _date_log = str(datetime.now().day).zfill(2) + '_' + str(datetime.now().month).zfill(2) + \
                    '_' + str(datetime.now().year)
            if mode == 'error':
                _date_log = 'errors'

            _path_logs = base_dir + '/log'
            self.filename = _path_logs + '/' + _date_log + '.log'
            self.msg = msg
            self.nam_f = obj_name[0]
            self.nam_m = obj_name[1]
            self.num_line = obj_name[2]

        except Exception as e:
            print(str(e))

    @pyqtSlot()
    def run(self):
        try:
            with open(self.filename, 'a') as file:
                temp_str = str(datetime.now())[:-3] + ' - [' + str(self.nam_f) + '].' + self.nam_m + \
                    '[' + str(self.num_line) + '] - ' + self.msg + '\n'
                file.write(temp_str)

        except Exception as err:
            print(str(err))


class Connection(QRunnable):
    signals = ReadSignals()

    def __init__(self, ip, port):
        super(Connection, self).__init__()
        self.ip = ip
        self.port = port
        self.startConnect()

    @pyqtSlot()
    def run(self):
        try:
            while self.cycle:
                while not self.flag_connect:
                    time.sleep(1)
                    self.startConnect()

                while self.flag_connect:
                    try:
                        msg = self.sock.recv(1024)
                        print(msg)
                        if msg == b'':
                            time.sleep(1)
                            txt_log = 'Соединение с сервером разорвано'
                            self.signals.result_log_connect.emit(txt_log)
                            self.flag_connect = False
                            self.sock.close()
                            self.startConnect()

                        elif msg == b'Hello! ASU server welcomes you!':
                            self.sock.send(b'Connection OK')
                            txt_log = 'Соединение с сервером установлено'
                            self.signals.result_log_connect.emit(txt_log)

                        elif msg[:3] == b'KAM':
                            temp_list = msg.decode(encoding='utf-8').split(',')
                            camera = int(temp_list[1])
                            command = temp_list[2]
                            if command == 'ON':
                                self.signals.connect_check.emit(camera, True)
                            if command == 'OFF':
                                self.signals.connect_check.emit(camera, False)
                            if command == 'DATA':
                                self.signals.connect_data.emit(camera)

                    except Exception as e:
                        self.signals.error_read.emit(e)
                        self.flag_connect = False
                        self.sock.close()

        except Exception as e:
            self.signals.error_read.emit(e)

    def startConnect(self):
        try:
            self.cycle = True
            self.flag_connect = False
            self.sock = socket.socket()
            self.sock.connect((self.ip, self.port))
            txt_log = 'Соединение с сервером..'
            self.signals.result_log_connect.emit(txt_log)
            self.flag_connect = True

        except Exception as e:
            self.flag_connect = False
            txt_log = 'Соединение потеряно'
            self.sock.close()
            self.signals.result_log_connect.emit(txt_log)
            self.signals.error_read.emit(e)

    def sendData(self, msg):
        self.sock.send(msg)
        txt_log = 'Посылка отправлена на сервер: ' + str(datetime.now())[:-7]
        self.signals.result_log_connect.emit(txt_log)

    def closeConnect(self):
        self.cycle = False
        self.sock.close()
        txt_log = 'Разрыв соединения'
        self.signals.result_log_connect.emit(txt_log)


class Writer(QRunnable):
    signals = ReadSignals()

    def __init__(self, client, adr_dev, command):
        super(Writer, self).__init__()
        self.client = client
        self.adr_dev = adr_dev
        self.command = command

    @pyqtSlot()
    def run(self):
        try:
            if self.command:
                rq = self.client.write_registers(8192, [1], slave=self.adr_dev)
                if not rq.isError():
                    txt_log = 'Попытка подключения Базовой станции №' + str(self.adr_dev)
                else:
                    txt_log = 'Неудачная попытка подключения Базовой станции №' + str(self.adr_dev)
                    self.signals.check_cell.emit(self.adr_dev, False)

            else:
                rq = self.client.write_registers(8192, [0], slave=self.adr_dev)
                if not rq.isError():
                    txt_log = 'Попытка отключения Базовой станции №' + str(self.adr_dev)
                else:
                    txt_log = 'Неудачная попытка отключения Базовой станции №' + str(self.adr_dev)
                    self.signals.check_cell.emit(self.adr_dev, True)
            Reader.signals.result_log.emit(txt_log)

        except ModEx as e:
            self.signals.error_modbus.emit(e)
            time.sleep(1)

        except Exception as e:
            self.signals.error_read.emit(e)


class Reader(QRunnable):
    signals = ReadSignals()

    def __init__(self, client, cell_list):
        super(Reader, self).__init__()
        self.cycle = True
        self.is_run = False
        self.client = client
        self.is_paused = False
        self.is_killed = False
        self.start_reg = 4101
        # self.sens_regs = [4103, 4108, 4113]
        self.cell_list = cell_list

    @pyqtSlot()
    def run(self):
        while self.cycle:
            try:
                if not self.is_run:
                    time.sleep(1)
                else:
                    for i in range(len(self.cell_list)):
                        cell_num = int(self.cell_list[i])
                        temp_arr = []
                        rr = self.client.read_holding_registers(8192, 1, slave=cell_num)
                        time.sleep(0.1)
                        if not rr.isError():
                            if rr.registers[0] == 1:
                                self.signals.check_cell.emit(cell_num, True)
                                state = 'on'
                                start_reg = 4121
                                for j in range(2):
                                    rr = self.client.read_holding_registers(start_reg, 60, slave=cell_num)
                                    for reg in range(0, len(rr.registers), 5):
                                        temp_list = []
                                        temper = self.dopCodeBintoDec('Temp', bin(rr.registers[reg + 2])[2:].zfill(16))
                                        temp_list.append(temper)
                                        serial = self.dopCodeBintoDec('Serial', bin(rr.registers[reg + 3])[2:].zfill(16))
                                        temp_list.append(serial)
                                        volt = self.dopCodeBintoDec('Bat', bin(rr.registers[reg + 4])[2:].zfill(8))
                                        temp_list.append(volt)

                                        temp_arr.append(temp_list)
                                    start_reg = 4181

                            else:
                                self.signals.check_cell.emit(cell_num, False)
                                state = 'off'
                                for j in range(3):
                                    temp_arr.append(['off', 'off', 'off'])

                        else:
                            txt_log = 'Базовая станция №' + str(i) + ' не отвечает'
                            self.signals.result_log.emit(txt_log)
                            state = 'err'
                            for j in range(3):
                                temp_arr.append(['err', 'err', 'err'])

                        self.signals.result_temp.emit(cell_num, state, temp_arr)
                        time.sleep(0.1)

            except ModEx as e:
                self.signals.error_modbus.emit(str(e))
                time.sleep(1)

            except Exception as e:
                self.signals.error_read.emit(e)

    def startProcess(self):
        self.cycle = True
        self.is_run = True
        txt_log = 'Процесс чтения запущен'
        self.signals.result_log.emit(txt_log)

    def exitProcess(self):
        self.cycle = False
        txt_log = 'Выход из процесса чтения'
        self.signals.result_log.emit(txt_log)

    def dopCodeBintoDec(self, command, value, bits=16):
        """Переводит бинарную строку в двоичном коде в десятичное число"""
        try:
            if value[0] == '1':
                val_temp = -(2 ** bits - int(value, 2))
            else:
                val_temp = int(value, 2)

            if command == 'Temp':
                val_temp = round(val_temp / 16, 1)
                if val_temp < -125 or val_temp > 125:
                    return '-----'

            if command == 'Serial':
                if val_temp < 1 or val_temp > 30000:
                    return '-----'

            if command == 'Bat':
                val_temp = round(val_temp * 0.1, 1)
                if val_temp < 0.1 or val_temp > 4.9:
                    return '-----'

            return str(val_temp)

        except Exception as e:
            self.signals.error_read.emit(e)
