import ctypes as c
from ctypes.util import find_library

lib_path = find_library('usbpt104')
libusbpt104 = c.cdll.LoadLibrary(lib_path)
libusbpt104.UsbPt104Enumerate.argtypes = [c.POINTER(c.c_char),
                                          c.POINTER(c.c_ulong),
                                          c.c_short]

libusbpt104.UsbPt104OpenUnit.argtypes = [c.POINTER(c.c_short),
                                         c.POINTER(c.c_char)]

libusbpt104.UsbPt104CloseUnit.argtypes = [c.c_short]


def open_unit(batch_and_serial):
    handle = c.c_short()
    batch_and_serial = batch_and_serial.encode()
    status = libusbpt104.UsbPt104OpenUnit(c.byref(handle), batch_and_serial)
    if status != 0:
        raise Exception(f'PICO ERROR WITH CODE {status}')

    print(f'Handle for {batch_and_serial.decode()} is {handle}')

    return handle


def discover_devices():
    enum_len = c.c_ulong(256)
    enum_string = c.create_string_buffer(256)
    communication_type = c.c_short()
    communication_type.value = 3
    libusbpt104.UsbPt104Enumerate(enum_string, enum_len,
                                  communication_type)

    devices = enum_string.value.decode().split(',')
    print(devices)


discover_devices()
SN_3 = 'EY477/080'
SN_2 = 'FO527/106'
SN_1 = 'EY477/119'

handle_1 = open_unit(SN_1)
handle_2 = open_unit(SN_2)
handle_3 = open_unit(SN_3)

libusbpt104.UsbPt104CloseUnit(handle_1)
print(f'Closing {SN_1}')

handle_1 = open_unit(SN_1)
