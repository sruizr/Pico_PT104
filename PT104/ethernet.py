import socket
import time
import threading
from queue import Queue
from . import PicoException, DataTypes, PicoStatus, Wires, PicoInfo
from .PT import PTCalculator
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


pt_calculator = PTCalculator(1)


class ChannelCalculator:
    def __init__(self, calibration, data_type, wires):
        self.wires = wires
        self.calibration = calibration
        self.data_type = data_type

    def get_value(self):
        measurements = self.measurements
        if DataTypes.OFF:
            raise PicoException(PicoStatus.PICO_NO_SAMPLES_AVAILABLE)

        temperature_types = [DataTypes.PT100, DataTypes.PT1000]
        res_types = [DataTypes.RESISTANCE_TO_10K, DataTypes.RESISTANCE_TO_375R]
        # voltage_types = [DataTypes.DIFFERENTIAL_TO_2500MV, DataTypes.DIFFERENTIAL_TO_115MV,
        #                  DataTypes.SINGLE_ENDED_TO_115W, DataTypes.SINGLE_ENDED_TO_2500MV]
        if self.data_type in res_types or self.data_type in temperature_types:
            if self.wires == Wires.WIRES_3:

                # For 3 wire
                resistance = (
                    self.calibration *
                    ((measurements[3] - (measurements[2] - measurements[1])) - measurements[2])
                ) /
                (measurements[1] - measurements[0])
            else:
                # For 2 and 4 wire
                resistance = (self.calibration * (measurements[3] - measurements[2]))/(measurements[1] - measurements[0])
        else:   # Voltage_types
            raise NotImplementedError()

        if self.data_type in [DataTypes.PT100, DataTypes.PT1000]:
            adim_res = (resistance / 100 if self.data_type == DataTypes.PT100
                        else resistance / 1000)
            return PtCalculator.get_temperature(adim_res)


class Connection(threading.Thread):
    _channel_headers = (0, 4, 8, 12)

    COMMANDS = {
        'LOCK': b'lock',
        'FREQ': b'\x30',
        'CONVERT': b'\x31',
        'EPROM': b'\x32',
        'UNLOCK': b'\x33',
        'ALIVE': b'\x34'
    }

    def __init__(self, address):
        super().__init__()
        self._last_alive = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(3)
        address = address.split(':')
        if len(address) == 1:
            address.append(25)
        address[1] = int(address[1])

        self.sock.connect(tuple(address))

        self._continue = True
        self.calculator  = Calculator()
        self.setDaemon(True)
        self._converting = False
        self._commands = Queue()
        self.exception = None

    def _run_command(request, expected_response):
        args = self._commands.get(block=False)
        if args:
            observer, request, process_response = args
            self.socket.send(request)
            response = self.socket.recv(1024)
            process_response(response)

    def run(self):
        while self._continue:
            try:
                self._keep_alive()
                self._run_command()
                if self.is_converting:
                    self.process_measurement()
            except Exception as e:
                self.exception = e
                self.socket.close()
                raise e
            time.sleep(0.01)

    def _keep_alive(self):
        if time.time() - self._last_alive > 10:
            self.socket.send(COMMANDS['ALIVE'])
            response = self.socket.recv(60)
            if response != b'Alive':
                raise PicoException(PicoStatus.PICO_NO_RESPONSE, self._sn,
                                    f'Response: {response}')
            self._last_alive = time.time()

    def process_measurement(self, data):
        data = self.socket.recv(20)
        if len(data) != 20:
            raise PicoException('INCORRECT_DATA', '{} with data'.format(self.socket))

        index = int(data[0] / 4)
        self.calculators[index].measurements = (
            int.from_bytes(data[1:5], 'big', signed=False),
            int.from_bytes(data[6:10], 'big', signed=False),
            int.from_bytes(data[11:15], 'big', signed=False),
            int.from_bytes(data[16:20], 'big', signed=False)
        )

    def close(self):
        self._commands.put(self._COMMANDS['UNLOCK'], self._close)

    def _close(self, response):
        if response != b'Unlocked':
            raise PicoException(f'Socket can not be unlocked: {response}')
        self.is_converting = False
        self._continue = False
        self.join()
        self.socket.close()

    def get_value(self, channel, low_pass_filter=False):
        if low_pass_filter:
            raise PicoException('Ethernet inferface has not low_pass_filter')
        return self.channels[channel].value

    def convert(self, channels=None):
        if channels:
            self.channels = channels
        arg = 0x00
        for channel in self.channels.values():
            if channel.data_type != DataTypes.OFF:
                arg |= 2**(channel.number - 1)
        event = threading.Event()
        self._commands.put(
            (self._COMMANDS['CONVERT'] + arg, self._convert, event)
        )
        event.wait()

    def _convert(self, response, event):
        if
        self.socket.send(self._COMMANDS['CONVERT'] + arg)
        self._converting = True

    def get_info(self):
        if not self._info:
            self._read_eeprom()

        if self._info and key in self._info:
            return self._info.get(key)

    def _read_eeprom(self):
        self.socket.send(COMMANDS['EPROM'])
        data = self.socket.recv(256)
        if data[:7] != b'Eeprom=':
            raise PicoException(PicoStatus.PICO_EEPROM_CORRUPT, data)

        data = data[7:]
        self._info['batch_and_serial'] = data[19:29].decode()
        self._info['cal_date'] = data[29:37].decode()
        calibrations = (
            int.from_bytes(data[37:41], 'little', signed=False),
            int.from_bytes(data[41:45], 'little', signed=False),
            int.from_bytes(data[45:49], 'little', signed=False),
            int.from_bytes(data[49:53], 'little', signed=False)
        )
        self._info['mac_address'] = data[53:59]

        for channel in self.channels.values():
            channel.calibration = calibrations[channel.number - 1]

    def set_mains(self, sixty_hertz):
        value = 0x00
        if sixty_hertz:
            value = 0xFF
        event = threading.Event()
        self._commands.put(
            (self._COMMANDS['FREQ'] + value, self._set_mains, event)
        )
        event.wait()

    def _set_mains(self, response, event):
        if response != b'Mains Changed':
            self.exception = PicoException(
                PicoStatus.PICO_CONFIG_FAIL, self._id,
                f'Response is {response}, but should be "Mains Changed"'
            )
            raise self.exception

        event.set()


class EthernetInterface:
    _CONNECTIONS = {}

    def _get_conn(self, address):
        connection = self._CONNECTIONS.get(address)
        if connection is None:
            raise PicoException(PicoStatus.PICO_NOT_FOUND, address)

    def open_unit(self, address):
        connection = Connection(address)
        self._CONNECTIONS[address] = connection
        return address

    def close_unit(self, address):
        connection = self._CONNECTIONS.pop(address)
        connection.close()

    def convert(self, address, channels):
        conn = self._get_conn(address)
        conn.convert(channels)
        if conn.exception:
            raise conn.exception

    def get_value(self, address, channel, low_pass_filter=False):
        conn = self._get_conn(address)
        value = conn.get_value(channel)
        if conn.exception:
            raise conn.exception
        return value

    def set_mains(self, address, sixty_hertz=False):
        conn = self._get_conn(address)
        conn.set_mains(sixty_hertz)
        if conn.exception:
            raise conn.exception

    def get_unit_info(self, address):
        conn = self._get_conn(address)
        info = conn.get_info()
        if conn.exception:
            raise conn.exception
        return info
