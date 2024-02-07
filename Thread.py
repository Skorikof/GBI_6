import time
import os
import socket
from datetime import datetime
from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
from pymodbus.exceptions import ModbusException as ModEx


base_dir = os.path.dirname(__file__)


class ReadSignals(QObject):
    thread_log = pyqtSignal(object)
    thread_error = pyqtSignal(object)
    read_result = pyqtSignal(int, list)
    connect_data = pyqtSignal(int)
    check_cell = pyqtSignal(int, bool)


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
                        # print(msg)
                        if msg == b'':
                            time.sleep(1)
                            txt_log = 'Соединение с сервером разорвано'
                            self.signals.thread_log.emit(txt_log)
                            self.flag_connect = False
                            self.sock.close()
                            self.startConnect()

                        elif msg == b'Hello! ASU server welcomes you!':
                            self.sock.send(b'Connection OK')
                            txt_log = 'Соединение с сервером установлено'
                            self.signals.thread_log.emit(txt_log)

                        elif msg[:3] == b'GET':
                            temp_list = msg.decode(encoding='utf-8').split(',')
                            span = int(temp_list[1])
                            command = temp_list[2]
                            if command == 'DATA':
                                self.signals.connect_data.emit(span)

                    except Exception as e:
                        self.signals.thread_error.emit(e)
                        self.flag_connect = False
                        self.sock.close()

        except Exception as e:
            self.signals.thread_error.emit(e)

    def startConnect(self):
        try:
            self.cycle = True
            self.flag_connect = False
            self.sock = socket.socket()
            self.sock.connect((self.ip, self.port))
            txt_log = 'Соединение с сервером..'
            self.signals.thread_log.emit(txt_log)
            self.flag_connect = True

        except Exception as e:
            self.flag_connect = False
            txt_log = 'Соединение потеряно'
            self.sock.close()
            self.signals.thread_log.emit(txt_log)
            self.signals.thread_error.emit(e)

    def sendData(self, msg):
        self.sock.send(msg)
        txt_log = 'Посылка отправлена на сервер: ' + str(datetime.now())[:-7]
        self.signals.thread_log.emit(txt_log)

    def closeConnect(self):
        self.cycle = False
        self.sock.close()
        txt_log = 'Разрыв соединения'
        self.signals.thread_log.emit(txt_log)


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
                time.sleep(0.1)
                if not rq.isError():
                    txt_log = 'Попытка подключения Базовой станции №' + str(self.adr_dev)
                else:
                    txt_log = 'Неудачная попытка подключения Базовой станции №' + str(self.adr_dev)
                    self.signals.check_cell.emit(self.adr_dev, False)

            else:
                rq = self.client.write_registers(8192, [0], slave=self.adr_dev)
                time.sleep(0.1)
                if not rq.isError():
                    txt_log = 'Попытка отключения Базовой станции №' + str(self.adr_dev)
                else:
                    txt_log = 'Неудачная попытка отключения Базовой станции №' + str(self.adr_dev)
                    self.signals.check_cell.emit(self.adr_dev, True)
            Reader.signals.thread_log.emit(txt_log)

        except ModEx as e:
            self.signals.thread_error.emit(e)
            txt_log = 'write thread'
            self.signals.thread_error.emit(txt_log)
            time.sleep(1)

        except Exception as e:
            self.signals.thread_error.emit(e)


class Reader(QRunnable):
    signals = ReadSignals()

    def __init__(self, client, count_span):
        super(Reader, self).__init__()
        self.cycle = True
        self.is_run = False
        self.client = client
        self.count_span = count_span
        self.is_paused = False
        self.is_killed = False

    @pyqtSlot()
    def run(self):
        while self.cycle:
            try:
                if not self.is_run:
                    time.sleep(1)
                else:
                    for i in range(1, self.count_span + 1):
                        adr_span = i

                        temp_arr = []
                        start_reg = 4121
                        for j in range(2):
                            rr = self.client.read_holding_registers(start_reg, 60, slave=adr_span)
                            if not rr.isError():
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
                                txt_log = 'Базовая станция №' + str(adr_span) + ' не отвечает'
                                self.signals.thread_log.emit(txt_log)

                        self.signals.read_result.emit(adr_span, temp_arr)
                        time.sleep(5)

            except ModEx as e:
                self.signals.thread_error.emit(str(e))
                txt_log = 'read thread'
                self.signals.thread_error.emit(txt_log)
                time.sleep(1)

            except Exception as e:
                self.signals.thread_error.emit(e)

    def startProcess(self):
        self.cycle = True
        self.is_run = True
        txt_log = 'Процесс чтения запущен'
        self.signals.thread_log.emit(txt_log)

    def exitProcess(self):
        self.cycle = False
        txt_log = 'Выход из процесса чтения'
        self.signals.thread_log.emit(txt_log)

    def dopCodeBintoDec(self, command, value, bits=16):
        """Переводит бинарную строку в двоичном коде в десятичное число"""
        try:
            if value[0] == '1':
                val_temp = -(2 ** bits - int(value, 2))
            else:
                val_temp = int(value, 2)

            if command == 'Temp':
                val_temp = round(val_temp / 16, 1)
                if val_temp <= 1 or val_temp > 125:
                    return '1000'

            if command == 'Serial':
                if val_temp <= 1 or val_temp > 1000:
                    return '1000'

            if command == 'Bat':
                val_temp = round(val_temp * 0.1, 1)
                if val_temp <= 1 or val_temp > 4.9:
                    return '1000'

            return str(val_temp)

        except Exception as e:
            self.signals.thread_error.emit(e)
