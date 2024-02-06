import inspect
import time
from Thread import LogWriter, Reader, Writer, Connection
from ReadSettings import COMSettings, DataSpan, DataSens, Registers
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
            if self.set_port.count_span == 1:
                QTabWidget.setTabVisible(self.ui.tabWidget, 1, False)
                self.check_cams(1, True)

            elif self.set_port.count_span == 2:
                QTabWidget.setTabVisible(self.ui.tabWidget, 1, True)
                self.check_cams(1, True)
                time.sleep(0.1)
                self.check_cams(2, True)

            self.dataCam = DataSpan()
            for i in range(int(self.set_port.count_span)):
                self.dataCam.span.append(DataSens())
                for j in range(24):
                    self.dataCam.span[i].sens.append(Registers())

        except Exception as e:
            self.saveLog('error', str(e))

    def thread_log(self, text):
        self.ui.info_set_label.setText(text)
        print(text)
        if self.set_port.create_log == '1':
            self.saveLog('info', text)

    def thread_error(self, text):
        print(text)
        self.ui.info_label.setText(str(text))
        self.saveLog('error', str(text))

    def initSocket(self):
        try:
            self.connect = Connection(self.set_port.IP_adr, self.set_port.local_port)
            self.connect.signals.thread_log_connect.connect(self.thread_log)
            self.connect.signals.thread_error.connect(self.thread_error)
            self.connect.signals.check_cell.connect(self.check_cams)
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

    def sendData(self, span):
        try:
            list_msg = []

            for i in range(24):
                list_msg.append(self.dataCam.span[span - 3].sens[i].temp)
                list_msg.append(self.dataCam.span[span - 3].sens[i].serial)
                list_msg.append(self.dataCam.span[span - 3].sens[i].bat)

            msg = b'DATA,' + str(span).encode(encoding='utf-8')

            for i in range(len(list_msg)):
                msg = msg + b',' + list_msg[i].encode(encoding='utf-8')

            self.signals.signalSendData.emit(msg)
            # print('Send msg --> {}'.format(msg))

        except Exception as e:
            self.saveLog('error', str(e))

    def threadInit(self):
        try:
            self.reader = Reader(self.set_port.client, self.set_port.count_span)
            self.reader.signals.read_result.connect(self.readResult)
            self.reader.signals.thread_error.connect(self.thread_error)
            self.reader.signals.thread_log.connect(self.thread_log)
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
        if self.set_port.count_span == 1:
            self.check_cams(1, False)
        elif self.set_port.count_span == 2:
            self.check_cams(1, False)
            self.check_cams(2, False)

    def check_cams(self, adr, state):
        try:
            self.writer = Writer(self.set_port.client, adr, state)
            self.threadpool.start(self.writer)

        except Exception as e:
            self.saveLog('error', str(e))

    def readResult(self, span, arr):
        try:
            txt_log = 'Посылка от Базовой станции {} получена: {}'.format(span, str(datetime.now())[:-7])
            self.ui.info_label.setText(txt_log)
            if self.set_port.create_log == '1':
                self.saveLog('info', txt_log)

            for i in range(len(arr)):
                self.fill_obj_data(span, i, arr[i])

        except Exception as e:
            self.saveLog('error', str(e))

    def fill_obj_data(self, span, sens, arr):
        try:
            self.dataCam.span[span - 1].sens[sens].temp = arr[0]
            self.dataCam.span[span - 1].sens[sens].serial = arr[1]
            self.dataCam.span[span - 1].sens[sens].bat = arr[2]

        except Exception as e:
            self.saveLog('error', str(e))
