import sys
import time

from Controller import ChangeUi
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QStyle, QAction, QMenu, qApp
from PyQt5.QtCore import QEvent


class ApplicationWindow(ChangeUi):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.initTray()
        self.tray_icon.show()

    def initTray(self):
        try:
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
            self.tray_icon.setToolTip('Температура бетона')
            show_action = QAction("Развернуть программу", self)
            quit_action = QAction("Выход из программы", self)
            show_action.triggered.connect(self.showNormal)
            quit_action.triggered.connect(self.closeEvent)
            tray_menu = QMenu()
            tray_menu.addAction(show_action)
            tray_menu.addAction(quit_action)
            self.tray_icon.setContextMenu(tray_menu)

        except Exception as e:
            self.saveLog('error', str(e))

    def changeEvent(self, event):
        try:
            if event.type() == QEvent.WindowStateChange:
                if self.isMinimized():
                    self.hide()
                    self.tray_icon.show()
                else:
                    self.tray_icon.hide()

        except Exception as e:
            self.saveLog('error', str(e))

    def closeEvent(self, event):
        try:
            if self.isVisible():
                # event.ignore()
                self.hide()
                self.tray_icon.show()

            else:
                self.tray_icon.hide()
                print('Threads working: ', str(self.threadpool.activeThreadCount()))
                self.exitThread()
                self.closeConnect()
                self.threadpool.waitForDone()
                print('Threads working: ', str(self.threadpool.activeThreadCount()))
                self.set_port.client.close()
                if self.set_port.create_log == '1':
                    self.saveLog('info', 'Выход из программы')
                qApp.quit()

        except Exception as e:
            self.saveLog('error', str(e))


def main():
    app = QApplication(sys.argv)
    window = ApplicationWindow()
    if window.set_port.start_up_position == '1':
        window.show()
    txt_log = 'Программа запущена'
    print(txt_log)
    try:
        window.startParam()
        time.sleep(1)
        window.threadInit()
        if window.set_port.connect_to_server == '1':
            window.initSocket()

    except Exception as e:
        window.saveLog('error', str(e))

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
