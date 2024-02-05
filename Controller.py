import inspect
import time
from Thread import LogWriter, Reader, Writer, Connection
from ReadSettings import COMSettings, DataCam, DataSens, Registers
from datetime import datetime
from MainUi import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QTabWidget
from PyQt5.QtCore import QObject, pyqtSignal, QThreadPool


class WindowSignals(QObject):
    signalStart = pyqtSignal()
    signalConnect = pyqtSignal()
    signalSendData = pyqtSignal(object)
    signalPause = pyqtSignal()
    signalExit = pyqtSignal()
    signalDisconnect = pyqtSignal()


class ChangeUi(QMainWindow):
    def __init__(self):
        super(ChangeUi, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.signals = WindowSignals()
        self.set_port = COMSettings()
        self.threadpool = QThreadPool()

    def saveLog(self, mode_s, msg_s):
        try:
            current_frame = inspect.currentframe()
            caller_frame = current_frame.f_back
            num_line = caller_frame.f_lineno
            code_obj = caller_frame.f_code
            code_obj_name = code_obj.co_name
            temp_str = code_obj.co_filename
            temp_d = temp_str.split('/')
            nam_f = temp_d[len(temp_d) - 1]

            self.logWriter = LogWriter(mode_s, (nam_f, code_obj_name, num_line), msg_s)
            self.threadpool.start(self.logWriter)

        except Exception as e:
            print(str(e))

    def startParam(self):
        try:
            self.ui.tabWidget.setCurrentIndex(0)
            if self.set_port.count_span == '1':
                QTabWidget.setTabVisible(self.ui.tabWidget, 1, False)

            if self.set_port.count_span == '2':
                QTabWidget.setTabVisible(self.ui.tabWidget, 1, True)

            self.cell_list = self.set_port.cell_list.split(',')

            # for i in range(len(self.cell_list)):
            #     self.check_cams(int(self.cell_list[i]), False)
            #     time.sleep(0.01)
            # time.sleep(0.01)

            self.dataCam = DataCam()
            for i in range(16):
                self.dataCam.cam.append(DataSens())
                for j in range(3):
                    self.dataCam.cam[i].sens.append(Registers())
                    self.dataCam.cam[i].sens[j].temp = '0'
                    self.dataCam.cam[i].sens[j].serial = '000'
                    self.dataCam.cam[i].sens[j].bat = '0'

        except Exception as e:
            self.saveLog('error', str(e))

    def initSocket(self):
        try:
            self.connect = Connection(self.set_port.IP_adr, self.set_port.local_port)
            self.connect.signals.result_log_connect.connect(self.readLogConnect)
            self.connect.signals.connect_check.connect(self.check_cams)
            self.connect.signals.connect_data.connect(self.sendData)
            self.signals.signalConnect.connect(self.connect.startConnect)
            self.signals.signalDisconnect.connect(self.connect.closeConnect)
            self.signals.signalSendData.connect(self.connect.sendData)
            self.threadpool.start(self.connect)

        except Exception as e:
            self.saveLog('error', str(e))

    def startConnect(self):
        self.signals.signalConnect.emit()

    def closeConnect(self):
        self.signals.signalDisconnect.emit()

    def sendData(self, camera):
        try:
            list_msg = []
            if str(camera) not in self.cell_list:
                state = 'err'
                list_msg = ['-----', '-----', '-----']

            else:
                state = self.dataCam.cam[camera - 1].state
                for i in range(len(self.dataCam.cam[camera - 1].data_list)):
                    for j in range(3):
                        list_msg.append(self.dataCam.cam[camera - 1].data_list[i][j])

            msg = b'DATA,' + str(camera).encode(encoding='utf-8')
            msg = msg + b',' + state.encode(encoding='utf-8')

            for i in range(len(list_msg)):
                msg = msg + b',' + list_msg[i].encode(encoding='utf-8')

            self.signals.signalSendData.emit(msg)

        except Exception as e:
            self.saveLog('error', str(e))

    def readLogConnect(self, text):
        self.ui.info_set_label.setText(text)
        print(text)
        if self.set_port.create_log == '1':
            self.saveLog('info', text)

    def threadInit(self):
        try:
            self.reader = Reader(self.set_port.client, self.cell_list)
            self.reader.signals.result_temp.connect(self.readResult)
            self.reader.signals.check_cell.connect(self.cancel_check)
            self.reader.signals.error_read.connect(self.readError)
            self.reader.signals.error_modbus.connect(self.readErrorModBus)
            self.reader.signals.result_log.connect(self.readLog)
            self.signals.signalStart.connect(self.reader.startProcess)
            self.signals.signalExit.connect(self.reader.exitProcess)
            self.threadpool.start(self.reader)
            self.startThread()

        except Exception as e:
            self.saveLog('error', str(e))

    def startThread(self):
        self.signals.signalStart.emit()

    def exitThread(self):
        self.signals.signalExit.emit()

    def readLog(self, text):
        self.ui.info_label.setText(text)
        print(text)
        if self.set_port.create_log == '1':
            self.saveLog('info', text)

    def readError(self, text):
        print(text)
        self.ui.info_label.setText(str(text))
        self.saveLog('error', str(text))

    def readErrorModBus(self, text):
        print(text)
        self.ui.info_label.setText(str(text))
        self.saveLog('error', str(text))

    def initCheck(self):
        try:
            self.ui.por1_cam1_checkBox.stateChanged.connect(lambda: self.check_cams(1,
                                                            self.ui.por1_cam1_checkBox.isChecked()))
            self.ui.por1_cam2_checkBox.stateChanged.connect(lambda: self.check_cams(2,
                                                            self.ui.por1_cam2_checkBox.isChecked()))
            self.ui.por1_cam3_checkBox.stateChanged.connect(lambda: self.check_cams(3,
                                                            self.ui.por1_cam3_checkBox.isChecked()))
            self.ui.por1_cam4_checkBox.stateChanged.connect(lambda: self.check_cams(4,
                                                            self.ui.por1_cam4_checkBox.isChecked()))
            self.ui.por1_cam5_checkBox.stateChanged.connect(lambda: self.check_cams(5,
                                                            self.ui.por1_cam5_checkBox.isChecked()))
            self.ui.por1_cam6_checkBox.stateChanged.connect(lambda: self.check_cams(6,
                                                            self.ui.por1_cam6_checkBox.isChecked()))
            self.ui.por1_cam7_checkBox.stateChanged.connect(lambda: self.check_cams(7,
                                                            self.ui.por1_cam7_checkBox.isChecked()))
            self.ui.por1_cam8_checkBox.stateChanged.connect(lambda: self.check_cams(8,
                                                            self.ui.por1_cam8_checkBox.isChecked()))

            self.ui.por2_cam1_checkBox.stateChanged.connect(lambda: self.check_cams(9,
                                                            self.ui.por2_cam1_checkBox.isChecked()))
            self.ui.por2_cam2_checkBox.stateChanged.connect(lambda: self.check_cams(10,
                                                            self.ui.por2_cam2_checkBox.isChecked()))
            self.ui.por2_cam3_checkBox.stateChanged.connect(lambda: self.check_cams(11,
                                                            self.ui.por2_cam3_checkBox.isChecked()))
            self.ui.por2_cam4_checkBox.stateChanged.connect(lambda: self.check_cams(12,
                                                            self.ui.por2_cam4_checkBox.isChecked()))
            self.ui.por2_cam5_checkBox.stateChanged.connect(lambda: self.check_cams(13,
                                                            self.ui.por2_cam5_checkBox.isChecked()))
            self.ui.por2_cam6_checkBox.stateChanged.connect(lambda: self.check_cams(14,
                                                            self.ui.por2_cam6_checkBox.isChecked()))
            self.ui.por2_cam7_checkBox.stateChanged.connect(lambda: self.check_cams(15,
                                                            self.ui.por2_cam7_checkBox.isChecked()))
            self.ui.por2_cam8_checkBox.stateChanged.connect(lambda: self.check_cams(16,
                                                            self.ui.por2_cam8_checkBox.isChecked()))

        except Exception as e:
            self.saveLog('error', str(e))

    def check_cams(self, adr, state):
        try:
            if str(adr) not in self.cell_list:
                pass

                # msg = b'ERROR,Incorrect camera number!'.encode(encoding='utf-8')
                #
                # self.signals.signalSendData.emit(msg)

            else:
                self.writer = Writer(self.set_port.client, adr, state)
                self.threadpool.start(self.writer)

        except Exception as e:
            self.saveLog('error', str(e))

    def cancel_check(self, adr, command):
        try:
            if adr == 1:
                if command:
                    self.ui.por1_cam1_checkBox.setChecked(True)
                else:
                    self.ui.por1_cam1_checkBox.setChecked(False)
            if adr == 2:
                if command:
                    self.ui.por1_cam2_checkBox.setChecked(True)
                else:
                    self.ui.por1_cam2_checkBox.setChecked(False)
            if adr == 3:
                if command:
                    self.ui.por1_cam3_checkBox.setChecked(True)
                else:
                    self.ui.por1_cam3_checkBox.setChecked(False)
            if adr == 4:
                if command:
                    self.ui.por1_cam4_checkBox.setChecked(True)
                else:
                    self.ui.por1_cam4_checkBox.setChecked(False)
            if adr == 5:
                if command:
                    self.ui.por1_cam5_checkBox.setChecked(True)
                else:
                    self.ui.por1_cam5_checkBox.setChecked(False)
            if adr == 6:
                if command:
                    self.ui.por1_cam6_checkBox.setChecked(True)
                else:
                    self.ui.por1_cam6_checkBox.setChecked(False)
            if adr == 7:
                if command:
                    self.ui.por1_cam7_checkBox.setChecked(True)
                else:
                    self.ui.por1_cam7_checkBox.setChecked(False)
            if adr == 8:
                if command:
                    self.ui.por1_cam8_checkBox.setChecked(True)
                else:
                    self.ui.por1_cam8_checkBox.setChecked(False)

            if adr == 9:
                if command:
                    self.ui.por2_cam1_checkBox.setChecked(True)
                else:
                    self.ui.por2_cam1_checkBox.setChecked(False)
            if adr == 10:
                if command:
                    self.ui.por2_cam2_checkBox.setChecked(True)
                else:
                    self.ui.por2_cam2_checkBox.setChecked(False)
            if adr == 11:
                if command:
                    self.ui.por2_cam3_checkBox.setChecked(True)
                else:
                    self.ui.por2_cam3_checkBox.setChecked(False)
            if adr == 12:
                if command:
                    self.ui.por2_cam4_checkBox.setChecked(True)
                else:
                    self.ui.por2_cam4_checkBox.setChecked(False)
            if adr == 13:
                if command:
                    self.ui.por2_cam5_checkBox.setChecked(True)
                else:
                    self.ui.por2_cam5_checkBox.setChecked(False)
            if adr == 14:
                if command:
                    self.ui.por2_cam6_checkBox.setChecked(True)
                else:
                    self.ui.por2_cam6_checkBox.setChecked(False)
            if adr == 15:
                if command:
                    self.ui.por2_cam7_checkBox.setChecked(True)
                else:
                    self.ui.por2_cam7_checkBox.setChecked(False)
            if adr == 16:
                if command:
                    self.ui.por2_cam8_checkBox.setChecked(True)
                else:
                    self.ui.por2_cam8_checkBox.setChecked(False)

        except Exception as e:
            self.saveLog('error', str(e))

    def readResult(self, cam, state, arr):
        try:
            # print('Count sens list - {}'.format(len(arr)))
            # for cam_list in range(len(arr)):
            #     print(arr[cam_list])

            txt_log = 'Посылка от Базовой станции {} получена: {}'.format(cam, str(datetime.now())[:-7])
            self.ui.info_label.setText(txt_log)
            if self.set_port.create_log == '1':
                self.saveLog('info', txt_log)

            if state == 'err' or state == 'off':
                self.fill_obj_err_off(cam, state)

            elif state == 'on':
                data_list = self.discard_left_data(arr)
                self.dataCam.cam[cam - 1].state = state
                self.dataCam.cam[cam - 1].data_list = data_list
                self.find_sens_id(cam, data_list)

            self.monitorSerialPort1()
            self.setColorSerialPort1()
            self.monitorSerialPort2()
            self.setColorSerialPort2()

            self.monitorTempPort1()
            self.setColorTempPort1()
            self.monitorTempPort2()
            self.setColorTempPort2()

            self.monitorBatPort1()
            self.setColorBatPort1()
            self.monitorBatPort2()
            self.setColorBatPort2()

        except Exception as e:
            self.saveLog('error', str(e))

    def find_sens_id(self, cam, arr):
        try:
            for i in range(3):
                self.fill_obj_data(cam, i, ['-----', '-----', '-----'])
            for i in range(len(arr)):
                id_sens = int(str(arr[i][1])[:1:])
                self.fill_obj_data(cam, id_sens, arr[i])

        except Exception as e:
            self.saveLog('error', str(e))

    def fill_obj_data(self, cam, sens, arr):
        try:
            self.dataCam.cam[cam - 1].sens[sens - 1].temp = arr[0]
            self.dataCam.cam[cam - 1].sens[sens - 1].serial = arr[1]
            self.dataCam.cam[cam - 1].sens[sens - 1].bat = arr[2]

        except Exception as e:
            self.saveLog('error', str(e))

    def fill_obj_err_off(self, cam, state):
        try:
            self.dataCam.cam[cam - 1].state = state
            for i in range(3):
                self.dataCam.cam[cam - 1].sens[i].temp = state
                self.dataCam.cam[cam - 1].sens[i].serial = state
                self.dataCam.cam[cam - 1].sens[i].bat = state

        except Exception as e:
            self.saveLog('error', str(e))

    def discard_left_data(self, arr):
        try:
            data_list = []
            for i in range(len(arr)):
                if arr[i][0] != '-----':
                    data_list.append(arr[i])
                else:
                    pass

            return data_list

        except Exception as e:
            self.saveLog('error', str(e))

    def monitorSerialPort1(self):
        try:
            self.ui.por1_cam1_sens1serial_label.setText(self.dataCam.cam[0].sens[0].serial)
            self.ui.por1_cam1_sens2serial_label.setText(self.dataCam.cam[0].sens[1].serial)
            self.ui.por1_cam1_sens3serial_label.setText(self.dataCam.cam[0].sens[2].serial)

            self.ui.por1_cam2_sens1serial_label.setText(self.dataCam.cam[1].sens[0].serial)
            self.ui.por1_cam2_sens2serial_label.setText(self.dataCam.cam[1].sens[1].serial)
            self.ui.por1_cam2_sens3serial_label.setText(self.dataCam.cam[1].sens[2].serial)

            self.ui.por1_cam3_sens1serial_label.setText(self.dataCam.cam[2].sens[0].serial)
            self.ui.por1_cam3_sens2serial_label.setText(self.dataCam.cam[2].sens[1].serial)
            self.ui.por1_cam3_sens3serial_label.setText(self.dataCam.cam[2].sens[2].serial)

            self.ui.por1_cam4_sens1serial_label.setText(self.dataCam.cam[3].sens[0].serial)
            self.ui.por1_cam4_sens2serial_label.setText(self.dataCam.cam[3].sens[1].serial)
            self.ui.por1_cam4_sens3serial_label.setText(self.dataCam.cam[3].sens[2].serial)

            self.ui.por1_cam5_sens1serial_label.setText(self.dataCam.cam[4].sens[0].serial)
            self.ui.por1_cam5_sens2serial_label.setText(self.dataCam.cam[4].sens[1].serial)
            self.ui.por1_cam5_sens3serial_label.setText(self.dataCam.cam[4].sens[2].serial)

            self.ui.por1_cam6_sens1serial_label.setText(self.dataCam.cam[5].sens[0].serial)
            self.ui.por1_cam6_sens2serial_label.setText(self.dataCam.cam[5].sens[1].serial)
            self.ui.por1_cam6_sens3serial_label.setText(self.dataCam.cam[5].sens[2].serial)

            self.ui.por1_cam7_sens1serial_label.setText(self.dataCam.cam[6].sens[0].serial)
            self.ui.por1_cam7_sens2serial_label.setText(self.dataCam.cam[6].sens[1].serial)
            self.ui.por1_cam7_sens3serial_label.setText(self.dataCam.cam[6].sens[2].serial)

            self.ui.por1_cam8_sens1serial_label.setText(self.dataCam.cam[7].sens[0].serial)
            self.ui.por1_cam8_sens2serial_label.setText(self.dataCam.cam[7].sens[1].serial)
            self.ui.por1_cam8_sens3serial_label.setText(self.dataCam.cam[7].sens[2].serial)

        except Exception as e:
            self.saveLog('error', str(e))

    def setColorSerialPort1(self):
        try:
            self.ui.por1_cam1_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[0].sens[0].serial))
            self.ui.por1_cam1_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[0].sens[1].serial))
            self.ui.por1_cam1_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[0].sens[2].serial))

            self.ui.por1_cam2_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[1].sens[0].serial))
            self.ui.por1_cam2_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[1].sens[1].serial))
            self.ui.por1_cam2_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[1].sens[2].serial))

            self.ui.por1_cam3_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[2].sens[0].serial))
            self.ui.por1_cam3_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[2].sens[1].serial))
            self.ui.por1_cam3_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[2].sens[2].serial))

            self.ui.por1_cam4_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[3].sens[0].serial))
            self.ui.por1_cam4_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[3].sens[1].serial))
            self.ui.por1_cam4_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[3].sens[2].serial))

            self.ui.por1_cam5_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[4].sens[0].serial))
            self.ui.por1_cam5_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[4].sens[1].serial))
            self.ui.por1_cam5_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[4].sens[2].serial))

            self.ui.por1_cam6_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[5].sens[0].serial))
            self.ui.por1_cam6_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[5].sens[1].serial))
            self.ui.por1_cam6_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[5].sens[2].serial))

            self.ui.por1_cam7_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[6].sens[0].serial))
            self.ui.por1_cam7_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[6].sens[1].serial))
            self.ui.por1_cam7_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[6].sens[2].serial))

            self.ui.por1_cam8_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[7].sens[0].serial))
            self.ui.por1_cam8_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[7].sens[1].serial))
            self.ui.por1_cam8_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[7].sens[2].serial))

        except Exception as e:
            self.saveLog('error', str(e))

    def monitorSerialPort2(self):
        try:
            self.ui.por2_cam1_sens1serial_label.setText(self.dataCam.cam[8].sens[0].serial)
            self.ui.por2_cam1_sens2serial_label.setText(self.dataCam.cam[8].sens[1].serial)
            self.ui.por2_cam1_sens3serial_label.setText(self.dataCam.cam[8].sens[2].serial)

            self.ui.por2_cam2_sens1serial_label.setText(self.dataCam.cam[9].sens[0].serial)
            self.ui.por2_cam2_sens2serial_label.setText(self.dataCam.cam[9].sens[1].serial)
            self.ui.por2_cam2_sens3serial_label.setText(self.dataCam.cam[9].sens[2].serial)

            self.ui.por2_cam3_sens1serial_label.setText(self.dataCam.cam[10].sens[0].serial)
            self.ui.por2_cam3_sens2serial_label.setText(self.dataCam.cam[10].sens[1].serial)
            self.ui.por2_cam3_sens3serial_label.setText(self.dataCam.cam[10].sens[2].serial)

            self.ui.por2_cam4_sens1serial_label.setText(self.dataCam.cam[11].sens[0].serial)
            self.ui.por2_cam4_sens2serial_label.setText(self.dataCam.cam[11].sens[1].serial)
            self.ui.por2_cam4_sens3serial_label.setText(self.dataCam.cam[11].sens[2].serial)

            self.ui.por2_cam5_sens1serial_label.setText(self.dataCam.cam[12].sens[0].serial)
            self.ui.por2_cam5_sens2serial_label.setText(self.dataCam.cam[12].sens[1].serial)
            self.ui.por2_cam5_sens3serial_label.setText(self.dataCam.cam[12].sens[2].serial)

            self.ui.por2_cam6_sens1serial_label.setText(self.dataCam.cam[13].sens[0].serial)
            self.ui.por2_cam6_sens2serial_label.setText(self.dataCam.cam[13].sens[1].serial)
            self.ui.por2_cam6_sens3serial_label.setText(self.dataCam.cam[13].sens[2].serial)

            self.ui.por2_cam7_sens1serial_label.setText(self.dataCam.cam[14].sens[0].serial)
            self.ui.por2_cam7_sens2serial_label.setText(self.dataCam.cam[14].sens[1].serial)
            self.ui.por2_cam7_sens3serial_label.setText(self.dataCam.cam[14].sens[2].serial)

            self.ui.por2_cam8_sens1serial_label.setText(self.dataCam.cam[15].sens[0].serial)
            self.ui.por2_cam8_sens2serial_label.setText(self.dataCam.cam[15].sens[1].serial)
            self.ui.por2_cam8_sens3serial_label.setText(self.dataCam.cam[15].sens[2].serial)

        except Exception as e:
            self.saveLog('error', str(e))

    def setColorSerialPort2(self):
        try:
            self.ui.por2_cam1_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[8].sens[0].serial))
            self.ui.por2_cam1_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[8].sens[1].serial))
            self.ui.por2_cam1_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[8].sens[2].serial))

            self.ui.por2_cam2_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[9].sens[0].serial))
            self.ui.por2_cam2_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[9].sens[1].serial))
            self.ui.por2_cam2_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[9].sens[2].serial))

            self.ui.por2_cam3_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[10].sens[0].serial))
            self.ui.por2_cam3_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[10].sens[1].serial))
            self.ui.por2_cam3_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[10].sens[2].serial))

            self.ui.por2_cam4_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[11].sens[0].serial))
            self.ui.por2_cam4_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[11].sens[1].serial))
            self.ui.por2_cam4_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[11].sens[2].serial))

            self.ui.por2_cam5_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[12].sens[0].serial))
            self.ui.por2_cam5_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[12].sens[1].serial))
            self.ui.por2_cam5_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[12].sens[2].serial))

            self.ui.por2_cam6_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[13].sens[0].serial))
            self.ui.por2_cam6_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[13].sens[1].serial))
            self.ui.por2_cam6_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[13].sens[2].serial))

            self.ui.por2_cam7_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[14].sens[0].serial))
            self.ui.por2_cam7_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[14].sens[1].serial))
            self.ui.por2_cam7_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[14].sens[2].serial))

            self.ui.por2_cam8_sens1serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[15].sens[0].serial))
            self.ui.por2_cam8_sens2serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[15].sens[1].serial))
            self.ui.por2_cam8_sens3serial_label.setStyleSheet(self.colorLCD(self.dataCam.cam[15].sens[2].serial))

        except Exception as e:
            self.saveLog('error', str(e))

    def monitorTempPort1(self):
        try:
            self.ui.por1_cam1_sens1temp_lcdNum.display(self.dataCam.cam[0].sens[0].temp)
            self.ui.por1_cam1_sens2temp_lcdNum.display(self.dataCam.cam[0].sens[1].temp)
            self.ui.por1_cam1_sens3temp_lcdNum.display(self.dataCam.cam[0].sens[2].temp)

            self.ui.por1_cam2_sens1temp_lcdNum.display(self.dataCam.cam[1].sens[0].temp)
            self.ui.por1_cam2_sens2temp_lcdNum.display(self.dataCam.cam[1].sens[1].temp)
            self.ui.por1_cam2_sens3temp_lcdNum.display(self.dataCam.cam[1].sens[2].temp)

            self.ui.por1_cam3_sens1temp_lcdNum.display(self.dataCam.cam[2].sens[0].temp)
            self.ui.por1_cam3_sens2temp_lcdNum.display(self.dataCam.cam[2].sens[1].temp)
            self.ui.por1_cam3_sens3temp_lcdNum.display(self.dataCam.cam[2].sens[2].temp)

            self.ui.por1_cam4_sens1temp_lcdNum.display(self.dataCam.cam[3].sens[0].temp)
            self.ui.por1_cam4_sens2temp_lcdNum.display(self.dataCam.cam[3].sens[1].temp)
            self.ui.por1_cam4_sens3temp_lcdNum.display(self.dataCam.cam[3].sens[2].temp)

            self.ui.por1_cam5_sens1temp_lcdNum.display(self.dataCam.cam[4].sens[0].temp)
            self.ui.por1_cam5_sens2temp_lcdNum.display(self.dataCam.cam[4].sens[1].temp)
            self.ui.por1_cam5_sens3temp_lcdNum.display(self.dataCam.cam[4].sens[2].temp)

            self.ui.por1_cam6_sens1temp_lcdNum.display(self.dataCam.cam[5].sens[0].temp)
            self.ui.por1_cam6_sens2temp_lcdNum.display(self.dataCam.cam[5].sens[1].temp)
            self.ui.por1_cam6_sens3temp_lcdNum.display(self.dataCam.cam[5].sens[2].temp)

            self.ui.por1_cam7_sens1temp_lcdNum.display(self.dataCam.cam[6].sens[0].temp)
            self.ui.por1_cam7_sens2temp_lcdNum.display(self.dataCam.cam[6].sens[1].temp)
            self.ui.por1_cam7_sens3temp_lcdNum.display(self.dataCam.cam[6].sens[2].temp)

            self.ui.por1_cam8_sens1temp_lcdNum.display(self.dataCam.cam[7].sens[0].temp)
            self.ui.por1_cam8_sens2temp_lcdNum.display(self.dataCam.cam[7].sens[1].temp)
            self.ui.por1_cam8_sens3temp_lcdNum.display(self.dataCam.cam[7].sens[2].temp)

        except Exception as e:
            self.saveLog('error', str(e))

    def setColorTempPort1(self):
        try:
            self.ui.por1_cam1_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[0].sens[0].temp))
            self.ui.por1_cam1_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[0].sens[1].temp))
            self.ui.por1_cam1_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[0].sens[2].temp))

            self.ui.por1_cam2_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[1].sens[0].temp))
            self.ui.por1_cam2_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[1].sens[1].temp))
            self.ui.por1_cam2_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[1].sens[2].temp))

            self.ui.por1_cam3_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[2].sens[0].temp))
            self.ui.por1_cam3_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[2].sens[1].temp))
            self.ui.por1_cam3_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[2].sens[2].temp))

            self.ui.por1_cam4_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[3].sens[0].temp))
            self.ui.por1_cam4_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[3].sens[1].temp))
            self.ui.por1_cam4_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[3].sens[2].temp))

            self.ui.por1_cam5_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[4].sens[0].temp))
            self.ui.por1_cam5_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[4].sens[1].temp))
            self.ui.por1_cam5_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[4].sens[2].temp))

            self.ui.por1_cam6_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[5].sens[0].temp))
            self.ui.por1_cam6_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[5].sens[1].temp))
            self.ui.por1_cam6_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[5].sens[2].temp))

            self.ui.por1_cam7_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[6].sens[0].temp))
            self.ui.por1_cam7_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[6].sens[1].temp))
            self.ui.por1_cam7_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[6].sens[2].temp))

            self.ui.por1_cam8_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[7].sens[0].temp))
            self.ui.por1_cam8_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[7].sens[1].temp))
            self.ui.por1_cam8_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[7].sens[2].temp))

        except Exception as e:
            self.saveLog('error', str(e))

    def monitorTempPort2(self):
        try:
            self.ui.por2_cam1_sens1temp_lcdNum.display(self.dataCam.cam[8].sens[0].temp)
            self.ui.por2_cam1_sens2temp_lcdNum.display(self.dataCam.cam[8].sens[1].temp)
            self.ui.por2_cam1_sens3temp_lcdNum.display(self.dataCam.cam[8].sens[2].temp)

            self.ui.por2_cam2_sens1temp_lcdNum.display(self.dataCam.cam[9].sens[0].temp)
            self.ui.por2_cam2_sens2temp_lcdNum.display(self.dataCam.cam[9].sens[1].temp)
            self.ui.por2_cam2_sens3temp_lcdNum.display(self.dataCam.cam[9].sens[2].temp)

            self.ui.por2_cam3_sens1temp_lcdNum.display(self.dataCam.cam[10].sens[0].temp)
            self.ui.por2_cam3_sens2temp_lcdNum.display(self.dataCam.cam[10].sens[1].temp)
            self.ui.por2_cam3_sens3temp_lcdNum.display(self.dataCam.cam[10].sens[2].temp)

            self.ui.por2_cam4_sens1temp_lcdNum.display(self.dataCam.cam[11].sens[0].temp)
            self.ui.por2_cam4_sens2temp_lcdNum.display(self.dataCam.cam[11].sens[1].temp)
            self.ui.por2_cam4_sens3temp_lcdNum.display(self.dataCam.cam[11].sens[2].temp)

            self.ui.por2_cam5_sens1temp_lcdNum.display(self.dataCam.cam[12].sens[0].temp)
            self.ui.por2_cam5_sens2temp_lcdNum.display(self.dataCam.cam[12].sens[1].temp)
            self.ui.por2_cam5_sens3temp_lcdNum.display(self.dataCam.cam[12].sens[2].temp)

            self.ui.por2_cam6_sens1temp_lcdNum.display(self.dataCam.cam[13].sens[0].temp)
            self.ui.por2_cam6_sens2temp_lcdNum.display(self.dataCam.cam[13].sens[1].temp)
            self.ui.por2_cam6_sens3temp_lcdNum.display(self.dataCam.cam[13].sens[2].temp)

            self.ui.por2_cam7_sens1temp_lcdNum.display(self.dataCam.cam[14].sens[0].temp)
            self.ui.por2_cam7_sens2temp_lcdNum.display(self.dataCam.cam[14].sens[1].temp)
            self.ui.por2_cam7_sens3temp_lcdNum.display(self.dataCam.cam[14].sens[2].temp)

            self.ui.por2_cam8_sens1temp_lcdNum.display(self.dataCam.cam[15].sens[0].temp)
            self.ui.por2_cam8_sens2temp_lcdNum.display(self.dataCam.cam[15].sens[1].temp)
            self.ui.por2_cam8_sens3temp_lcdNum.display(self.dataCam.cam[15].sens[2].temp)

        except Exception as e:
            self.saveLog('error', str(e))

    def setColorTempPort2(self):
        try:
            self.ui.por2_cam1_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[8].sens[0].temp))
            self.ui.por2_cam1_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[8].sens[1].temp))
            self.ui.por2_cam1_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[8].sens[2].temp))

            self.ui.por2_cam2_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[9].sens[0].temp))
            self.ui.por2_cam2_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[9].sens[1].temp))
            self.ui.por2_cam2_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[9].sens[2].temp))

            self.ui.por2_cam3_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[10].sens[0].temp))
            self.ui.por2_cam3_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[10].sens[1].temp))
            self.ui.por2_cam3_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[10].sens[2].temp))

            self.ui.por2_cam4_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[11].sens[0].temp))
            self.ui.por2_cam4_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[11].sens[1].temp))
            self.ui.por2_cam4_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[11].sens[2].temp))

            self.ui.por2_cam5_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[12].sens[0].temp))
            self.ui.por2_cam5_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[12].sens[1].temp))
            self.ui.por2_cam5_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[12].sens[2].temp))

            self.ui.por2_cam6_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[13].sens[0].temp))
            self.ui.por2_cam6_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[13].sens[1].temp))
            self.ui.por2_cam6_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[13].sens[2].temp))

            self.ui.por2_cam7_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[14].sens[0].temp))
            self.ui.por2_cam7_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[14].sens[1].temp))
            self.ui.por2_cam7_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[14].sens[2].temp))

            self.ui.por2_cam8_sens1temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[15].sens[0].temp))
            self.ui.por2_cam8_sens2temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[15].sens[1].temp))
            self.ui.por2_cam8_sens3temp_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[15].sens[2].temp))

        except Exception as e:
            self.saveLog('error', str(e))

    def monitorBatPort1(self):
        try:
            self.ui.por1_cam1_sens1bat_lcdNum.display(self.dataCam.cam[0].sens[0].bat)
            self.ui.por1_cam1_sens2bat_lcdNum.display(self.dataCam.cam[0].sens[1].bat)
            self.ui.por1_cam1_sens3bat_lcdNum.display(self.dataCam.cam[0].sens[2].bat)

            self.ui.por1_cam2_sens1bat_lcdNum.display(self.dataCam.cam[1].sens[0].bat)
            self.ui.por1_cam2_sens2bat_lcdNum.display(self.dataCam.cam[1].sens[1].bat)
            self.ui.por1_cam2_sens3bat_lcdNum.display(self.dataCam.cam[1].sens[2].bat)

            self.ui.por1_cam3_sens1bat_lcdNum.display(self.dataCam.cam[2].sens[0].bat)
            self.ui.por1_cam3_sens2bat_lcdNum.display(self.dataCam.cam[2].sens[1].bat)
            self.ui.por1_cam3_sens3bat_lcdNum.display(self.dataCam.cam[2].sens[2].bat)

            self.ui.por1_cam4_sens1bat_lcdNum.display(self.dataCam.cam[3].sens[0].bat)
            self.ui.por1_cam4_sens2bat_lcdNum.display(self.dataCam.cam[3].sens[1].bat)
            self.ui.por1_cam4_sens3bat_lcdNum.display(self.dataCam.cam[3].sens[2].bat)

            self.ui.por1_cam5_sens1bat_lcdNum.display(self.dataCam.cam[4].sens[0].bat)
            self.ui.por1_cam5_sens2bat_lcdNum.display(self.dataCam.cam[4].sens[1].bat)
            self.ui.por1_cam5_sens3bat_lcdNum.display(self.dataCam.cam[4].sens[2].bat)

            self.ui.por1_cam6_sens1bat_lcdNum.display(self.dataCam.cam[5].sens[0].bat)
            self.ui.por1_cam6_sens2bat_lcdNum.display(self.dataCam.cam[5].sens[1].bat)
            self.ui.por1_cam6_sens3bat_lcdNum.display(self.dataCam.cam[5].sens[2].bat)

            self.ui.por1_cam7_sens1bat_lcdNum.display(self.dataCam.cam[6].sens[0].bat)
            self.ui.por1_cam7_sens2bat_lcdNum.display(self.dataCam.cam[6].sens[1].bat)
            self.ui.por1_cam7_sens3bat_lcdNum.display(self.dataCam.cam[6].sens[2].bat)

            self.ui.por1_cam8_sens1bat_lcdNum.display(self.dataCam.cam[7].sens[0].bat)
            self.ui.por1_cam8_sens2bat_lcdNum.display(self.dataCam.cam[7].sens[1].bat)
            self.ui.por1_cam8_sens3bat_lcdNum.display(self.dataCam.cam[7].sens[2].bat)

        except Exception as e:
            self.saveLog('error', str(e))

    def setColorBatPort1(self):
        try:
            self.ui.por1_cam1_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[0].sens[0].bat))
            self.ui.por1_cam1_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[0].sens[1].bat))
            self.ui.por1_cam1_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[0].sens[2].bat))

            self.ui.por1_cam2_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[1].sens[0].bat))
            self.ui.por1_cam2_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[1].sens[1].bat))
            self.ui.por1_cam2_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[1].sens[2].bat))

            self.ui.por1_cam3_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[2].sens[0].bat))
            self.ui.por1_cam3_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[2].sens[1].bat))
            self.ui.por1_cam3_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[2].sens[2].bat))

            self.ui.por1_cam4_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[3].sens[0].bat))
            self.ui.por1_cam4_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[3].sens[1].bat))
            self.ui.por1_cam4_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[3].sens[2].bat))

            self.ui.por1_cam5_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[4].sens[0].bat))
            self.ui.por1_cam5_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[4].sens[1].bat))
            self.ui.por1_cam5_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[4].sens[2].bat))

            self.ui.por1_cam6_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[5].sens[0].bat))
            self.ui.por1_cam6_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[5].sens[1].bat))
            self.ui.por1_cam6_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[5].sens[2].bat))

            self.ui.por1_cam7_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[6].sens[0].bat))
            self.ui.por1_cam7_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[6].sens[1].bat))
            self.ui.por1_cam7_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[6].sens[2].bat))

            self.ui.por1_cam8_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[7].sens[0].bat))
            self.ui.por1_cam8_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[7].sens[1].bat))
            self.ui.por1_cam8_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[7].sens[2].bat))

        except Exception as e:
            self.saveLog('error', str(e))

    def monitorBatPort2(self):
        try:
            self.ui.por2_cam1_sens1bat_lcdNum.display(self.dataCam.cam[8].sens[0].bat)
            self.ui.por2_cam1_sens2bat_lcdNum.display(self.dataCam.cam[8].sens[1].bat)
            self.ui.por2_cam1_sens3bat_lcdNum.display(self.dataCam.cam[8].sens[2].bat)

            self.ui.por2_cam2_sens1bat_lcdNum.display(self.dataCam.cam[9].sens[0].bat)
            self.ui.por2_cam2_sens2bat_lcdNum.display(self.dataCam.cam[9].sens[1].bat)
            self.ui.por2_cam2_sens3bat_lcdNum.display(self.dataCam.cam[9].sens[2].bat)

            self.ui.por2_cam3_sens1bat_lcdNum.display(self.dataCam.cam[10].sens[0].bat)
            self.ui.por2_cam3_sens2bat_lcdNum.display(self.dataCam.cam[10].sens[1].bat)
            self.ui.por2_cam3_sens3bat_lcdNum.display(self.dataCam.cam[10].sens[2].bat)

            self.ui.por2_cam4_sens1bat_lcdNum.display(self.dataCam.cam[11].sens[0].bat)
            self.ui.por2_cam4_sens2bat_lcdNum.display(self.dataCam.cam[11].sens[1].bat)
            self.ui.por2_cam4_sens3bat_lcdNum.display(self.dataCam.cam[11].sens[2].bat)

            self.ui.por2_cam5_sens1bat_lcdNum.display(self.dataCam.cam[12].sens[0].bat)
            self.ui.por2_cam5_sens2bat_lcdNum.display(self.dataCam.cam[12].sens[1].bat)
            self.ui.por2_cam5_sens3bat_lcdNum.display(self.dataCam.cam[12].sens[2].bat)

            self.ui.por2_cam6_sens1bat_lcdNum.display(self.dataCam.cam[13].sens[0].bat)
            self.ui.por2_cam6_sens2bat_lcdNum.display(self.dataCam.cam[13].sens[1].bat)
            self.ui.por2_cam6_sens3bat_lcdNum.display(self.dataCam.cam[13].sens[2].bat)

            self.ui.por2_cam7_sens1bat_lcdNum.display(self.dataCam.cam[14].sens[0].bat)
            self.ui.por2_cam7_sens2bat_lcdNum.display(self.dataCam.cam[14].sens[1].bat)
            self.ui.por2_cam7_sens3bat_lcdNum.display(self.dataCam.cam[14].sens[2].bat)

            self.ui.por2_cam8_sens1bat_lcdNum.display(self.dataCam.cam[15].sens[0].bat)
            self.ui.por2_cam8_sens2bat_lcdNum.display(self.dataCam.cam[15].sens[1].bat)
            self.ui.por2_cam8_sens3bat_lcdNum.display(self.dataCam.cam[15].sens[2].bat)

        except Exception as e:
            self.saveLog('error', str(e))

    def setColorBatPort2(self):
        try:
            self.ui.por2_cam1_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[8].sens[0].bat))
            self.ui.por2_cam1_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[8].sens[1].bat))
            self.ui.por2_cam1_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[8].sens[2].bat))

            self.ui.por2_cam2_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[9].sens[0].bat))
            self.ui.por2_cam2_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[9].sens[1].bat))
            self.ui.por2_cam2_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[9].sens[2].bat))

            self.ui.por2_cam3_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[10].sens[0].bat))
            self.ui.por2_cam3_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[10].sens[1].bat))
            self.ui.por2_cam3_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[10].sens[2].bat))

            self.ui.por2_cam4_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[11].sens[0].bat))
            self.ui.por2_cam4_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[11].sens[1].bat))
            self.ui.por2_cam4_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[11].sens[2].bat))

            self.ui.por2_cam5_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[12].sens[0].bat))
            self.ui.por2_cam5_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[12].sens[1].bat))
            self.ui.por2_cam5_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[12].sens[2].bat))

            self.ui.por2_cam6_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[13].sens[0].bat))
            self.ui.por2_cam6_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[13].sens[1].bat))
            self.ui.por2_cam6_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[13].sens[2].bat))

            self.ui.por2_cam7_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[14].sens[0].bat))
            self.ui.por2_cam7_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[14].sens[1].bat))
            self.ui.por2_cam7_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[14].sens[2].bat))

            self.ui.por2_cam8_sens1bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[15].sens[0].bat))
            self.ui.por2_cam8_sens2bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[15].sens[1].bat))
            self.ui.por2_cam8_sens3bat_lcdNum.setStyleSheet(self.colorLCD(self.dataCam.cam[15].sens[2].bat))

        except Exception as e:
            self.saveLog('error', str(e))

    def colorLCD(self, data):
        try:
            color = 'color: rgb(25, 30, 115);'
            if data == 'off':
                color = 'color: rgb(0, 0, 0);'
            if data == 'err':
                color = 'color: rgb(255, 0, 0);'
            if data == '-----':
                color = 'color: rgb(255, 0, 0);'
            return color

        except Exception as e:
            self.saveLog('error', str(e))