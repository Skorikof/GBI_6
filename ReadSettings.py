import configparser
from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.framer import ModbusAsciiFramer as Framer


class COMSettings(object):
    """Чтение настроек СОМ порта из файла ini"""

    def __init__(self):
        try:
            config = configparser.ConfigParser()
            config.read("Settings.ini")
            self.portNumber = 'COM' + config["ComPort"]["NumberPort"]
            temp_val = config["ComPort"]["PortSettings"]
            temp_com = str.split(temp_val, ",")
            self.portSpeed = int(temp_com[0])
            self.portParity = temp_com[1]
            self.portDataBits = temp_com[2]
            self.portStopBits = temp_com[3]
            self.client = None

            self.IP_adr = config["Local"]["IP_Address"]
            self.local_port = int(config["Local"]["Port"])
            self.start_up_position = config["PrgSet"]["StartUpPosition"]
            self.connect_to_server = config["PrgSet"]["ConnectToServer"]
            self.count_span = config["PrgSet"]["CountSpan"]
            self.create_log = config["PrgSet"]["CreateLogFile"]
            self.cell_list = config["PrgSet"]["CellList"]

            a = self.initPort()

        except Exception as e:
            print(str(e))

    def initPort(self):
        try:
            self.client = ModbusClient(framer=Framer, port=str(self.portNumber),
                                       timeout=1, baudrate=int(self.portSpeed),
                                       stopbits=int(self.portStopBits),
                                       parity=str(self.portParity), strict=False)

            self.port_connect = self.client.connect()

            if self.port_connect:
                return True
            else:
                return False

        except Exception as e:
            print(str(e))


class Registers(object):
    def __init__(self):
        self.temp = '-10'
        self.serial = '-10'
        self.bat = '-10'


class DataSens(object):
    def __init__(self):
        self.sens = []
        self.state = 'off'
        self.data_list = []


class DataCam(object):
    def __init__(self):
        self.cam = []
