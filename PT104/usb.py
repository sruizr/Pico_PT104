import ctypes as c
from ctypes.util import find_library
from . import (PicoException, Channels, PicoInfo, CommunicationType, DataTypes,
               PicoStatus)


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class USBdriver(metaclass=Singleton):
    def __init__(self):
        # load the shared library
        lib_path = find_library('usbpt104')
        if lib_path is None:
            raise OSError('shared library usbpt104 not found')
        else:
            self.lib = c.cdll.LoadLibrary(lib_path)

            # define function argument types
            # Close the port (do this each time you finish using the device!)
            self.lib.UsbPt104CloseUnit.argtypes = [c.c_short]
            # This function returns a list of all the attached PT-104 devices of the specified port type
            self.lib.UsbPt104Enumerate.argtypes = [c.POINTER(c.c_char),
                                                      c.POINTER(c.c_ulong),
                                                      CommunicationType]

            # This function obtains information on a specified device.
            self.lib.UsbPt104GetUnitInfo.argtypes = [c.c_short, c.POINTER(c.c_char),
                                                        c.c_short, c.POINTER(c.c_short), PicoInfo]

            # Get the most recent data reading from a channel.
            self.lib.UsbPt104GetValue.argtypes = [c.c_short, Channels,
                                                     c.POINTER(c.c_long), c.c_short]

            # Open the device through its USB interface.
            self.lib.UsbPt104OpenUnit.argtypes = [c.POINTER(c.c_short),
                                                     c.POINTER(c.c_char)]

            # Specify the sensor type and filtering for a channel.
            self.lib.UsbPt104SetChannel.argtypes = [c.c_short, Channels, DataTypes,
                                                       c.c_short]

            # This function is used to inform the driver of the local mains (line) frequency. This helps the driver to filter
            # out electrical noise.
            self.lib.UsbPt104SetMains.argtypes = [c.c_short, c.c_ushort]

            self.lib.UsbPt104IpDetails.argtypes = [c.c_short, c.POINTER(c.c_short),
                                                      c.POINTER(c.c_char),
                                                      c.POINTER(c.c_long),
                                                      c.POINTER(c.c_long), c.c_short]



class USBinterface:
    class __USBinterface:
        """Interface between connection and PT104 using a USB
        """
        _HANDLES = {}
        _FACTORS = {}

        def __init__(self):
            self.driver = USBdriver()
            devices = self.discover_devices()
            devices = [device[4:] for device in devices if device[:4] == 'USB:']
            while devices:
                self.open_unit(devices.pop())



        def discover_devices(self, communication_type=CommunicationType.CT_USB):
            """This function returns a list of all the attached PT-104 devices of the specified port type

            :param communication_type: type of the devices to discover (COMMUNICATION_TYPE)
            :return: string
            """
            enum_len = c.c_ulong(256)
            enum_string = c.create_string_buffer(256)

            self.driver.lib.UsbPt104Enumerate(enum_string, enum_len,
                                          communication_type)
            enum  = enum_string.value.decode().split(',')
            return enum

        def _get_handle(self, batch_and_serial):
            handle = self._HANDLES.get(batch_and_serial)
            if handle is None:
                raise PicoException(PicoStatus.PICO_NOT_FOUND, batch_and_serial)
            return handle

        def open_unit(self, batch_and_serial):
            if batch_and_serial in self._HANDLES:
                return batch_and_serial

            handle = c.c_short()
            serial = (batch_and_serial.encode() if type(batch_and_serial) is str
                      else batch_and_serial)
            status = self.driver.lib.UsbPt104OpenUnit(c.byref(handle), serial)
            if status != 0:
                raise PicoException(status, batch_and_serial)

            handles = [handle.value for handle in  self._HANDLES.values()]
            if handle.value in handles:  # Handle is repeated driver
                raise PicoException(PicoStatus.PICO_NOT_FOUND, batch_and_serial)
            else:
                self._HANDLES[batch_and_serial] = handle

            self._FACTORS[batch_and_serial] = [1] * 4
            return batch_and_serial

        def get_ip_details(self, batch_and_serial):
            handle = self._get_handle(batch_and_serial)
            idt_get = c.c_short(0)
            enabled = c.c_short()

            ip_address = c.create_string_buffer(256)
            address_len = c.c_long()
            port = c.c_long()

            self.driver.lib.UsbPt104IpDetails(handle, c.byref(enabled), ip_address,
                                          c.byref(address_len), c.byref(port),
                                          idt_get)
            return {'ip_address': ip_address.value,
                    'len': address_len.value,
                    'port': port.value,
                    'enabled': enabled.value == 1}

        def set_ip_details(self, batch_and_serial, ip_address, port):
            pass

        def disable_ip(self, batch_and_serial):
            pass

        def enable_ip(self, batch_and_serial):
            pass

        def close_unit(self, batch_and_serial):
            handle = self._get_handle(batch_and_serial)
            status = self.driver.lib.UsbPt104CloseUnit(handle)
            if status != 0:
                raise PicoException(status)

        def set_channel(self, batch_and_serial, channel_number, data_type, wires):
            handle = self._get_handle(batch_and_serial)
            status = self.driver.lib.UsbPt104SetChannel(
                handle, channel_number, data_type, wires
            )
            if status != 0:
                raise PicoException(status, batch_and_serial,
                                    f'Setting channel {channel_number}')

            self._FACTORS[batch_and_serial][channel_number - 1] = self._get_factor(
                data_type
            )

        def get_value(self, batch_and_serial, channel, low_pass_filter=False):
            measurement = c.c_long()
            handle = self._get_handle(batch_and_serial)
            status_channel = self.driver.lib.UsbPt104GetValue(
                handle, channel, c.byref(measurement), low_pass_filter
            )
            if status_channel != 0:
                raise PicoException(status_channel, batch_and_serial)

            return measurement.value * self._FACTORS[batch_and_serial][channel - 1]

        def _get_factor(self, data_type):
            """scales the value from the device.

            :param value: value to convert as float
            :param channel: channel number (Channels)
            :return: Temperature in °C, Resistance in mOhm, Voltage in mV
            """
            if data_type in [DataTypes.PT100, DataTypes.PT1000,
                             DataTypes.RESISTANCE_TO_375R]:
                return 1E-3
            if data_type == DataTypes.RESISTANCE_TO_10K:
                return 1.0
            if data_type in [DataTypes.DIFFERENTIAL_TO_115MV,
                             DataTypes.SINGLE_ENDED_TO_115MV]:
                return 1E-9  # mV
            if data_type in [DataTypes.DIFFERENTIAL_TO_2500MV,
                             DataTypes.SINGLE_ENDED_TO_2500MV]:
                return 1E-8  # mV
            if data_type == DataTypes.OFF:
                return 0

        def set_mains(self, batch_and_serial, sixty_hertz=False):
            handle = self._get_handle(batch_and_serial)
            if sixty_hertz:
                sixty_hertz = c.c_ushort(1)
            else:
                sixty_hertz = c.c_ushort(0)
            self.driver.lib.UsbPt104SetMains(handle, sixty_hertz)

        def _get_info(self, handle, info_id):
            info_len = c.c_short(256)
            info_string = c.create_string_buffer(256)
            req_len = c.c_short()
            self.driver.lib.UsbPt104GetUnitInfo(handle, info_string, info_len,
                                            c.byref(req_len), info_id)
            return info_string.value.decode()

        def get_info(self, batch_and_serial):
            handle = self._get_handle(batch_and_serial)
            info = {
                'driver_version': PicoInfo.PICO_DRIVER_VERSION,
                'usb_version': PicoInfo.PICO_USB_VERSION,
                'hardware_version': PicoInfo.PICO_HARDWARE_VERSION,
                'variant_info': PicoInfo.PICO_VARIANT_INFO,
                'batch_and_serial': PicoInfo.PICO_BATCH_AND_SERIAL,
                'cal_date': PicoInfo.PICO_CAL_DATE,
                'kernel_driver_version': PicoInfo.PICO_KERNEL_DRIVER_VERSION
            }

            return {key: self._get_info(handle, value)
                    for key, value in info.items()}

    instance = None
    def __init__(self):
        if not USBinterface.instance:
            USBinterface.instance = USBinterface.__USBinterface()

    def __getattr__(self, name):
        return getattr(self.instance, name)
