import ctypes as c
from ctypes.util import find_library
from . import (PicoException, Channels, PicoInfo, CommunicationType, DataTypes,
               PicoStatus)


# load the shared library
lib_path = find_library('usbpt104')
if lib_path is None:
    raise OSError('shared library usbpt104 not found')
else:
    libusbpt104 = c.cdll.LoadLibrary(lib_path)

    # define function argument types
    # Close the port (do this each time you finish using the device!)
    libusbpt104.UsbPt104CloseUnit.argtypes = [c.c_short]
    # This function returns a list of all the attached PT-104 devices of the specified port type
    libusbpt104.UsbPt104Enumerate.argtypes = [c.POINTER(c.c_char),
                                              c.POINTER(c.c_ulong),
                                              CommunicationType]

    # This function obtains information on a specified device.
    libusbpt104.UsbPt104GetUnitInfo.argtypes = [c.c_short, c.POINTER(c.c_char),
                                                c.c_short, c.POINTER(c.c_short), PicoInfo]

    # Get the most recent data reading from a channel.
    libusbpt104.UsbPt104GetValue.argtypes = [c.c_short, Channels,
                                             c.POINTER(c.c_long), c.c_short]

    # Open the device through its USB interface.
    libusbpt104.UsbPt104OpenUnit.argtypes = [c.POINTER(c.c_short),
                                             c.POINTER(c.c_char)]

    # Specify the sensor type and filtering for a channel.
    libusbpt104.UsbPt104SetChannel.argtypes = [c.c_short, Channels, DataTypes,
                                               c.c_short]

    # This function is used to inform the driver of the local mains (line) frequency. This helps the driver to filter
    # out electrical noise.
    libusbpt104.UsbPt104SetMains.argtypes = [c.c_short, c.c_ushort]


class USBinteface:
    """Interface between connection and PT104 using a USB
    """
    _HANDLES = {}

    def discover_devices(communication_type=CommunicationType.CT_USB):
        """This function returns a list of all the attached PT-104 devices of the specified port type

        :param communication_type: type of the devices to discover (COMMUNICATION_TYPE)
        :return: string
        """
        enum_len = c.c_ulong(256)
        enum_string = c.create_string_buffer(256)

        libusbpt104.UsbPt104Enumerate(enum_string, enum_len,
                                      communication_type)
        return enum_string.value

    def _get_handle(self, batch_and_serial):
        handle = self._HANDLES.get(batch_and_serial)
        if handle is None:
            raise PicoException(PicoStatus.PICO_NOT_FOUND, batch_and_serial)
        return handle

    def open_unit(self, batch_and_serial):
        handle = c.c_short()
        serial = (batch_and_serial.encode() if type(batch_and_serial) is str
                  else batch_and_serial)
        status = libusbpt104.UsbPt104OpenUnit(c.byref(handle), serial)
        if status != 0:
            raise PicoException(status, batch_and_serial)
        self._HANDLES[batch_and_serial] = handle

        return batch_and_serial

    def close_unit(self, batch_and_serial):
        handle = self._get_conn(batch_and_serial)
        status = libusbpt104.UsbPt104CloseUnit(handle)
        if status != 0:
            raise PicoException(status)

    def convert(self, batch_and_serial, channels):
        handle = self._get_handle(batch_and_serial)
        for channel in channels:
            status = libusbpt104.UsbPt104SetChannel(
                handle, channel.number, channel.data_type, channel.wires
            )
            if status != 0:
                raise PicoException(status, batch_and_serial,
                                    f'Setting channel {channel.number}')

    def get_value(self, batch_and_serial, channel, low_pass_filter=False):
        measurement = c.c_long()
        handle = self._get_handle(batch_and_serial)
        status_channel = libusbpt104.UsbPt104GetValue(
            handle, channel, c.byref(measurement), low_pass_filter
        )
        if status_channel != 0:
            raise PicoException(status_channel, batch_and_serial)

        return measurement.value

    def set_mains(self, batch_and_serial, sixty_hertz=False):
        handle = self._get_handle(batch_and_serial)
        if sixty_hertz:
            sixty_hertz = c.c_ushort(1)
        else:
            sixty_hertz = c.c_ushort(0)
        libusbpt104.UsbPt104SetMains(handle, sixty_hertz)

    def _get_info(self, handle, info_id):
        info_len = c.c_short(256)
        info_string = c.create_string_buffer(256)
        req_len = c.c_short()
        libusbpt104.UsbPt104GetUnitInfo(handle, info_string, info_len,
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
