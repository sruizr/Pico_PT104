""" A Wrapper around the usbpt104 library from Pico for the Pico PT-104A RTD DATA Acquisition Module

# -*- coding: utf-8 -*-
It also works for the Omega PT-104A.

Based on Code from:
https://www.picotech.com/support/topic27941.html
https://www.picotech.com/support/topic31981.html?sid=48264e01d90ccb6a8a72240a5d024ea6

Drivers for Linux can be found at:
https://www.picotech.com/downloads/linux

The API documentation:
https://www.picotech.com/download/manuals/usb-pt104-rtd-data-logger-programmers-guide.pdf

Example::

    from PT104 import PT104, Channels, DataTypes, Wires
    from PT104.usb import USBinterface

    interface = USBinterface()
    unit = PT104()
    unit.interface = interface

    unit.connect('AY429/026')
    unit.channels[1].data_type = DataTypes.PT100
    unit.channels[1].wires = Wires.WIRES_4
    unit.convert()

    value = unit.channels[1].value
    if value:
        print('CH1: %1.3f'%value)
    unit.disconnect()

"""
__author__ = "Martin Schröder"
__copyright__ = "Copyright 2018, Technische Universität Berlin"
__credits__ = []
__license__ = "GPLv3"
__version__ = "2.0.0"
__maintainer__ = "Salvador Ruiz"
__email__ = "m.schroeder@tu-berlin.de"
__status__ = "Beta"
__docformat__ = 'reStructuredText'


import time
from enum import IntEnum
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CtypesEnum(IntEnum):
    @classmethod
    def from_param(cls, obj):
        return int(obj)


class Channels(CtypesEnum):
    CHANNEL_1 = 1
    CHANNEL_2 = 2
    CHANNEL_3 = 3
    CHANNEL_4 = 4
    CHANNEL_5 = 5
    CHANNEL_6 = 6
    CHANNEL_7 = 7
    CHANNEL_8 = 8
    MAX_CHANNELS = CHANNEL_8


class Wires(CtypesEnum):
    WIRES_2 = 2
    WIRES_3 = 3
    WIRES_4 = 4
    MIN_WIRES = WIRES_2
    MAX_WIRES = WIRES_4


class DataTypes(CtypesEnum):
    OFF = 0
    PT100 = 1
    PT1000 = 2
    RESISTANCE_TO_375R = 3
    RESISTANCE_TO_10K = 4
    DIFFERENTIAL_TO_115MV = 5
    DIFFERENTIAL_TO_2500MV = 6
    SINGLE_ENDED_TO_115MV = 7
    SINGLE_ENDED_TO_2500MV = 8


class CommunicationType(CtypesEnum):
    CT_USB = 0x00000001
    CT_ETHERNET = 0x00000002
    CT_ALL = 0xFFFFFFFF


class PicoInfo(CtypesEnum):
    PICO_DRIVER_VERSION = 0
    PICO_USB_VERSION = 1
    PICO_HARDWARE_VERSION = 2
    PICO_VARIANT_INFO = 3
    PICO_BATCH_AND_SERIAL = 4
    PICO_CAL_DATE = 5
    PICO_KERNEL_DRIVER_VERSION = 6
    PICO_MAC_ADDRESS = 7


class PicoStatus(CtypesEnum):
    PICO_OK = 0x00000000
    PICO_MAX_UNITS_OPENED = 0x00000001
    PICO_MEMORY_FAIL = 0x00000002
    PICO_NOT_FOUND = 0x00000003
    PICO_FW_FAIL = 0x00000004
    PICO_OPEN_OPERATION_IN_PROGRESS = 0x00000005
    PICO_OPERATION_FAILED = 0x00000006
    PICO_NOT_RESPONDING = 0x00000007
    PICO_CONFIG_FAIL = 0x00000008
    PICO_KERNEL_DRIVER_TOO_OLD = 0x00000009
    PICO_EEPROM_CORRUPT = 0x0000000A
    PICO_OS_NOT_SUPPORTED = 0x0000000B
    PICO_INVALID_HANDLE = 0x0000000C
    PICO_INVALID_PARAMETER = 0x0000000D
    PICO_INVALID_TIMEBASE = 0x0000000E
    PICO_INVALID_VOLTAGE_RANGE = 0x0000000F
    PICO_INVALID_CHANNEL = 0x00000010
    PICO_INVALID_TRIGGER_CHANNEL = 0x00000011
    PICO_INVALID_CONDITION_CHANNEL = 0x00000012
    PICO_NO_SIGNAL_GENERATOR = 0x00000013
    PICO_STREAMING_FAILED = 0x00000014
    PICO_BLOCK_MODE_FAILED = 0x00000015
    PICO_NULL_PARAMETER = 0x00000016
    PICO_ETS_MODE_SET = 0x00000017
    PICO_DATA_NOT_AVAILABLE = 0x00000018
    PICO_STRING_BUFFER_TO_SMALL = 0x00000019
    PICO_ETS_NOT_SUPPORTED = 0x0000001A
    PICO_AUTO_TRIGGER_TIME_TO_SHORT = 0x0000001B
    PICO_BUFFER_STALL = 0x0000001C
    PICO_TOO_MANY_SAMPLES = 0x0000001D
    PICO_TOO_MANY_SEGMENTS = 0x0000001E
    PICO_PULSE_WIDTH_QUALIFIER = 0x0000001F
    PICO_DELAY = 0x00000020
    PICO_SOURCE_DETAILS = 0x00000021
    PICO_CONDITIONS = 0x00000022
    PICO_USER_CALLBACK = 0x00000023
    PICO_DEVICE_SAMPLING = 0x00000024
    PICO_NO_SAMPLES_AVAILABLE = 0x00000025
    PICO_SEGMENT_OUT_OF_RANGE = 0x00000026
    PICO_BUSY = 0x00000027
    PICO_STARTINDEX_INVALID = 0x00000028
    PICO_INVALID_INFO = 0x00000029
    PICO_INFO_UNAVAILABLE = 0x0000002A
    PICO_INVALID_SAMPLE_INTERVAL = 0x0000002B
    PICO_TRIGGER_ERROR = 0x0000002C
    PICO_MEMORY = 0x0000002D
    PICO_SIG_GEN_PARAM = 0x0000002E
    PICO_SHOTS_SWEEPS_WARNING = 0x0000002F
    PICO_SIGGEN_TRIGGER_SOURCE = 0x00000030
    PICO_AUX_OUTPUT_CONFLICT = 0x00000031
    PICO_AUX_OUTPUT_ETS_CONFLICT = 0x00000032
    PICO_WARNING_EXT_THRESHOLD_CONFLICT = 0x00000033
    PICO_WARNING_AUX_OUTPUT_CONFLICT = 0x00000034
    PICO_SIGGEN_OUTPUT_OVER_VOLTAGE = 0x00000035
    PICO_DELAY_NULL = 0x00000036
    PICO_INVALID_BUFFER = 0x00000037
    PICO_SIGGEN_OFFSET_VOLTAGE = 0x00000038
    PICO_SIGGEN_PK_TO_PK = 0x00000039
    PICO_CANCELLED = 0x0000003A
    PICO_SEGMENT_NOT_USED = 0x0000003B
    PICO_INVALID_CALL = 0x0000003C
    PICO_GET_VALUES_INTERRUPTED = 0x0000003D
    PICO_NOT_USED = 0x0000003F
    PICO_INVALID_SAMPLERATIO = 0x00000040
    PICO_INVALID_STATE = 0x00000041
    PICO_NOT_ENOUGH_SEGMENTS = 0x00000042
    PICO_DRIVER_FUNCTION = 0x00000043
    PICO_RESERVED = 0x00000044
    PICO_INVALID_COUPLING = 0x00000045
    PICO_BUFFERS_NOT_SET = 0x00000046
    PICO_RATIO_MODE_NOT_SUPPORTED = 0x00000047
    PICO_RAPID_NOT_SUPPORT_AGGREGATION = 0x00000048
    PICO_INVALID_TRIGGER_PROPERTY = 0x00000049
    PICO_INTERFACE_NOT_CONNECTED = 0x0000004A
    PICO_RESISTANCE_AND_PROBE_NOT_ALLOWED = 0x0000004B
    PICO_POWER_FAILED = 0x0000004C
    PICO_SIGGEN_WAVEFORM_SETUP_FAILED = 0x0000004D
    PICO_FPGA_FAIL = 0x0000004E
    PICO_POWER_MANAGER = 0x0000004F
    PICO_INVALID_ANALOGUE_OFFSET = 0x00000050
    PICO_PLL_LOCK_FAILED = 0x00000051
    PICO_ANALOG_BOARD = 0x00000052
    PICO_CONFIG_FAIL_AWG = 0x00000053
    PICO_INITIALISE_FPGA = 0x00000054
    PICO_EXTERNAL_FREQUENCY_INVALID = 0x00000056
    PICO_CLOCK_CHANGE_ERROR = 0x00000057
    PICO_TRIGGER_AND_EXTERNAL_CLOCK_CLASH = 0x00000058
    PICO_PWQ_AND_EXTERNAL_CLOCK_CLASH = 0x00000059
    PICO_UNABLE_TO_OPEN_SCALING_FILE = 0x0000005A
    PICO_MEMORY_CLOCK_FREQUENCY = 0x0000005B
    PICO_I2C_NOT_RESPONDING = 0x0000005C
    PICO_NO_CAPTURES_AVAILABLE = 0x0000005D
    PICO_NOT_USED_IN_THIS_CAPTURE_MODE = 0x0000005E
    PICO_TOO_MANY_TRIGGER_CHANNELS_IN_USE = 0x0000005F
    PICO_INVALID_TRIGGER_DIRECTION = 0x00000060
    PICO_INVALID_TRIGGER_STATES = 0x00000061
    PICO_GET_DATA_ACTIVE = 0x00000103
    PICO_IP_NETWORKED = 0x00000104
    PICO_INVALID_IP_ADDRESS = 0x00000105
    PICO_IPSOCKET_FAILED = 0x00000106
    PICO_IPSOCKET_TIMEDOUT = 0x00000107
    PICO_SETTINGS_FAILED = 0x00000108
    PICO_NETWORK_FAILED = 0x00000109
    PICO_WS2_32_DLL_NOT_LOADED = 0x0000010A
    PICO_INVALID_IP_PORT = 0x0000010B
    PICO_COUPLING_NOT_SUPPORTED = 0x0000010C
    PICO_BANDWIDTH_NOT_SUPPORTED = 0x0000010D
    PICO_INVALID_BANDWIDTH = 0x0000010E
    PICO_AWG_NOT_SUPPORTED = 0x0000010F
    PICO_ETS_NOT_RUNNING = 0x00000110
    PICO_SIG_GEN_WHITENOISE_NOT_SUPPORTED = 0x00000111
    PICO_SIG_GEN_WAVETYPE_NOT_SUPPORTED = 0x00000112
    PICO_INVALID_DIGITAL_PORT = 0x00000113
    PICO_INVALID_DIGITAL_CHANNEL = 0x00000114
    PICO_INVALID_DIGITAL_TRIGGER_DIRECTION = 0x00000115
    PICO_SIG_GEN_PRBS_NOT_SUPPORTED = 0x00000116
    PICO_ETS_NOT_AVAILABLE_WITH_LOGIC_CHANNELS = 0x00000117
    PICO_WARNING_REPEAT_VALUE = 0x00000118
    PICO_POWER_SUPPLY_CONNECTED = 0x00000119
    PICO_POWER_SUPPLY_NOT_CONNECTED = 0x0000011A
    PICO_POWER_SUPPLY_REQUEST_INVALID = 0x0000011B
    PICO_POWER_SUPPLY_UNDERVOLTAGE = 0x0000011C
    PICO_CAPTURING_DATA = 0x0000011D
    PICO_USB3_0_DEVICE_NON_USB3_0_PORT = 0x0000011E
    PICO_NOT_SUPPORTED_BY_THIS_DEVICE = 0x0000011F
    PICO_INVALID_DEVICE_RESOLUTION = 0x00000120
    PICO_INVALID_NUMBER_CHANNELS_FOR_RESOLUTION = 0x00000121
    PICO_CHANNEL_DISABLED_DUE_TO_USB_POWERED = 0x00000122
    PICO_SIGGEN_DC_VOLTAGE_NOT_CONFIGURABLE = 0x00000123
    PICO_NO_TRIGGER_ENABLED_FOR_TRIGGER_IN_PRE_TRIG = 0x00000124
    PICO_TRIGGER_WITHIN_PRE_TRIG_NOT_ARMED = 0x00000125
    PICO_TRIGGER_WITHIN_PRE_NOT_ALLOWED_WITH_DELAY = 0x00000126
    PICO_TRIGGER_INDEX_UNAVAILABLE = 0x00000127
    PICO_AWG_CLOCK_FREQUENCY = 0x00000128
    PICO_TOO_MANY_CHANNELS_IN_USE = 0x00000129
    PICO_NULL_CONDITIONS = 0x0000012A
    PICO_DUPLICATE_CONDITION_SOURCE = 0x0000012B
    PICO_INVALID_CONDITION_INFO = 0x0000012C
    PICO_SETTINGS_READ_FAILED = 0x0000012D
    PICO_SETTINGS_WRITE_FAILED = 0x0000012E
    PICO_ARGUMENT_OUT_OF_RANGE = 0x0000012F
    PICO_HARDWARE_VERSION_NOT_SUPPORTED = 0x00000130
    PICO_DIGITAL_HARDWARE_VERSION_NOT_SUPPORTED = 0x00000131
    PICO_ANALOGUE_HARDWARE_VERSION_NOT_SUPPORTED = 0x00000132
    PICO_UNABLE_TO_CONVERT_TO_RESISTANCE = 0x00000133
    PICO_DUPLICATED_CHANNEL = 0x00000134
    PICO_INVALID_RESISTANCE_CONVERSION = 0x00000135
    PICO_INVALID_VALUE_IN_MAX_BUFFER = 0x00000136
    PICO_INVALID_VALUE_IN_MIN_BUFFER = 0x00000137
    PICO_SIGGEN_FREQUENCY_OUT_OF_RANGE = 0x00000138
    PICO_EEPROM2_CORRUPT = 0x00000139
    PICO_EEPROM2_FAIL = 0x0000013A
    PICO_SERIAL_BUFFER_TOO_SMALL = 0x0000013B
    PICO_SIGGEN_TRIGGER_AND_EXTERNAL_CLOCK_CLASH = 0x0000013C
    PICO_WARNING_SIGGEN_AUXIO_TRIGGER_DISABLED = 0x0000013D
    PICO_SIGGEN_GATING_AUXIO_NOT_AVAILABLE = 0x00000013E
    PICO_SIGGEN_GATING_AUXIO_ENABLED = 0x00000013F
    PICO_DEVICE_TIME_STAMP_RESET = 0x01000000
    PICO_WATCHDOGTIMER = 0x10000000
    PICO_IPP_NOT_FOUND = 0x10000001
    PICO_IPP_ERROR = 0x10000003
    PICO_IPP_NO_FUNCTION = 0x10000002
    PICO_SHADOW_CAL_NOT_AVAILABLE = 0x10000004
    PICO_SHADOW_CAL_DISABLED = 0x10000005
    PICO_SHADOW_CAL_ERROR = 0x10000006
    PICO_SHADOW_CAL_CORRUPT = 0x10000007


class PicoException(Exception):
    def __init__(self, status_code, deviceid, more_info=None):
        self.status = PicoStatus(status_code)
        self.deviceid = deviceid
        self.more_info = more_info

        message = f'Device "{self.deviceid}" has raised {self.status.name}'
        if more_info:
            message += f', {more_info}'
        super().__init__(message)


class Channel:
    _UNITS = {
        DataTypes.OFF: '',
        DataTypes.PT100: '°C',
        DataTypes.PT1000: '°C',
        DataTypes.RESISTANCE_TO_375R: 'mOhm',
        DataTypes.RESISTANCE_TO_10K: 'mOhm',
        DataTypes.DIFFERENTIAL_TO_115MV: 'mV',
        DataTypes.DIFFERENTIAL_TO_2500MV: 'mV',
        DataTypes.SINGLE_ENDED_TO_115MV: 'mV',
        DataTypes.SINGLE_ENDED_TO_2500MV: 'mV'
    }

    def __init__(self, logger, number,
                 data_type=DataTypes.OFF,
                 wires=Wires.WIRES_2,
                 low_pass_filter=False):
        self.logger = logger
        self.number = number

        self._data_type = data_type
        self._wires = wires
        self.low_pass_filter = low_pass_filter
        self._next_query = None
        self._is_active = False

    @property
    def is_active(self):
        return self._is_active

    @property
    def data_type(self):
        return self._data_type

    @data_type.setter
    def data_type(self, value):
        if self._data_type != value:
            self._data_type = value

    @property
    def wires(self):
        return self._wires

    @wires.setter
    def wires(self, value):
        if self._wires != value:
            self._wires = value

    @property
    def units(self):
        return self._UNITS[self.data_type]

    @property
    def value(self):
        if not self._is_active:
            raise PicoException(
                PicoStatus.PICO_INVALID_CHANNEL, self.logger.id,
                f'Channel: {self.number}'
            )

        if self.data_type == DataTypes.OFF:
            raise PicoException(
                PicoStatus.PICO_NO_SAMPLES_AVAILABLE, self.logger.id,
                f'Channel: {self.number}'
            )

        self._wait_for_conversion()

        value = self.logger.get_value(self.number, self.low_pass_filter)
        return value

    def _wait_for_conversion(self):
        """wait until a new adc conversion is avalaible

        :param channel: channel number (Channels)
        :return:
        """
        while time.time() < self._next_query:
            time.sleep(0.01)
        self._next_query = (time.time() +
                            self.logger.active_channels_count * 0.75)

    def activate(self):
        self.logger.activate_channel(self.number)
        self._next_query = (time.time() + max(3,
                            1.7 * self.logger.active_channels_count))
        self._is_active = self.data_type != DataTypes.OFF

    def deactivate(self):
        self.logger.deactivate_channel(self.number)
        self._is_active = False


class PT104:
    def __init__(self, conn_string, interface=None):
        self._conn_string = conn_string
        self.interface = interface
        self.channels = {
            key: Channel(self, key)
            for key in [1, 2, 3, 4]
        }
        self.id = None
        self._info = {}

    @property
    def info(self):
        """This function obtains information on a specified device.

        :param print_result: also print the unit info to the console
        :return: the unit info as dict
        """
        if not self._info:
            self._info = self.interface.get_info(self.id)
        return self._info

    @property
    def is_connected(self):
        """returns the connection status

        :return: connection status
        """
        return self.id is not None

    def connect(self):
        """Connect to a PT-104A data acquisition module via USB or Ethernet

        .. note:: Ethernet connection is not implemented

        :param serial: serial number of the device
        :return: connection status
        """

        self.id = self.interface.open_unit(self._conn_string)

    @property
    def active_channels_count(self):
        """return the number of active channels

        :return: number of active channels
        """
        return sum([channel.is_active
                    for channel in self.channels.values()])

    def disconnect(self):
        """disconnect from the unit

        :return:
        """
        if not self.is_connected:
            return

        self.interface.close_unit(self.id)
        self.id = None
        self._info = {}

    def _assure_is_connected(self):
        if not self.is_connected:
            self.connect()

    def get_value(self, channel, lower_pass_filter=False):
        """queries the measurement value directly from inteface

        :param channel: channel number (Channels)
        :param raw_value: skip conversion
        :return: measured value
        """
        self._assure_is_connected()
        return self.interface.get_value(self.id, channel,
                                        lower_pass_filter)

    def activate_channel(self, channel_number):
        self._assure_is_connected()
        channel = self.channels[channel_number]
        self.interface.set_channel(self.id, channel.number, channel.data_type,
                                   channel.wires)

    def deactivate_channel(self, channel_number):
        self._assure_is_connected()
        channel = self.channels[channel_number]
        self.interface.set_channel(self.id, channel.number, DataTypes.OFF,
                                   channel.wires)

    def set_mains(self, sixty_hertz=False):
        self._assure_is_connected()
        """This function is used to inform the driver of the local mains (line) frequency.

        This helps the driver to filter out electrical noise.

        :param sixty_hertz: mains frequency is sixty
        :return: success
        """
        self.interface.set_mains(self.id, sixty_hertz)

    def clear(self):
        for channel in self.channels.values():
            if channel.is_active:
                channel.deactivate()

    def __del__(self):
        self.clear()
