from unittest.mock import Mock, patch
from PT104.usb import USBinteface


class A_USBinterface:
    @patch('PT104.usb.libusbpt104')
    @patch('PT104.usb.c')
    def should_open_unit(self, mock_c, mock_lib):
        interface = USBinteface()
        mock_lib.UsbPt104OpenUnit.return_value = 0

        value = interface.open_unit('tracking')

        assert value == 'tracking'
        mock_lib.UsbPt104OpenUnit.assert_called_with(
            mock_c.byref.return_value, b'tracking'
        )

    @patch('PT104.usb.libusbpt104')
    @patch('PT104.usb.c')
    def should_close_unit(self, mock_c, mock_lib):
        pass
