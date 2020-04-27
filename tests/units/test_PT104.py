from unittest.mock import Mock, patch
import time
from PT104 import PT104, DataTypes, Channel, PicoException, PicoStatus


class A_Channel:
    @patch('PT104.time')
    def should_supply_suitable_value(self, mock_time):
        logger = Mock()
        logger.get_value.return_value = 1.0
        logger.active_channel_count = 1
        mock_time.time.side_effect = range(100)

        channel = Channel(logger, 1)
        channel.updated()  # fakes converting cycle
        try:
            channel.value
        except PicoException as p:
            assert p.status == PicoStatus.PICO_NO_SAMPLES_AVAILABLE

        channel.data_type = DataTypes.PT100
        channel.updated()  # fakes converting cycle
        assert channel.value == 1e-3

        channel.data_type = DataTypes.PT1000
        channel.updated()  # fakes converting cycle
        assert channel.value == 1e-3

        channel.data_type = DataTypes.RESISTANCE_TO_375R
        channel.updated()  # fakes converting cycle
        assert channel.value == 1e-3

        channel.data_type = DataTypes.RESISTANCE_TO_10K
        channel.updated()  # fakes converting cycle
        assert channel.value == 1.0

        channel.data_type = DataTypes.DIFFERENTIAL_TO_115MV
        channel.updated()  # fakes converting cycle
        assert channel.value == 1e-9

        channel.data_type = DataTypes.DIFFERENTIAL_TO_2500MV
        channel.updated()  # fakes converting cycle
        assert channel.value == 1e-8

        channel.data_type = DataTypes.SINGLE_ENDED_TO_115MV
        channel.updated()  # fakes converting cycle
        assert channel.value == 1e-9

        channel.data_type = DataTypes.SINGLE_ENDED_TO_2500MV
        channel.updated()  # fakes converting cycle
        assert channel.value == 1e-8

    def should_raise_pico_exception_when_not_updated(self):
        logger = Mock()
        logger.get_value.return_value = 1.0
        logger.active_channel_count = 1
        channel = Channel(logger, 1)

        try:
            channel.value
        except PicoException as p:
            assert p.status == PicoStatus.PICO_INVALID_CHANNEL

    def should_wait_till_value_is_refreshed(self):
        logger = Mock()
        logger.get_value.return_value = 1.0
        logger.active_channel_count = 2
        channel = Channel(logger, 1)
        channel.data_type = DataTypes.PT100
        channel.updated()

        channel.value
        start = time.time()
        channel.value
        elapsed_time = time.time() - start

        assert round(elapsed_time, 2) == 1.5

    def should_supply_suitable_units(self):
        logger = Mock()
        channel = Channel(logger, 1)

        channel.data_type = DataTypes.PT100
        assert channel.units == '°C'

        channel.data_type = DataTypes.PT1000
        assert channel.units == '°C'

        channel.data_type = DataTypes.OFF
        assert channel.units == ''

        channel.data_type = DataTypes.RESISTANCE_TO_375R
        assert channel.units == 'mOhm'
        channel.data_type = DataTypes.RESISTANCE_TO_10K
        assert channel.units == 'mOhm'

        channel.data_type = DataTypes.DIFFERENTIAL_TO_115MV
        assert channel.units == 'mV'

        channel.data_type = DataTypes.DIFFERENTIAL_TO_2500MV
        assert channel.units == 'mV'

        channel.data_type = DataTypes.SINGLE_ENDED_TO_115MV
        assert channel.units == 'mV'

        channel.data_type = DataTypes.SINGLE_ENDED_TO_2500MV
        assert channel.units == 'mV'


class A_PT104:
    def should_get_info_from_interface(self):
        interface = Mock()
        id = interface.open_unit.return_value

        pt104 = PT104()
        pt104.interface = interface
        pt104.connect('tracking')

        info = pt104.info
        interface.get_info.assert_called_with(id)
        assert info == interface.get_info.return_value

    def should_connect_using_interface(self):
        interface = Mock()
        pt104 = PT104(interface)

        pt104.connect('tracking')

        interface.open_unit.assert_called_with('tracking')
        assert pt104.is_connected

    def should_count_acive_channels(self):
        interface = Mock()
        pt104 = PT104(interface)

        assert pt104.active_channel_count == 0
        pt104.channels[1].data_type = DataTypes.PT100
        assert pt104.active_channel_count == 1

    def should_disconnect(self):
        interface = Mock()
        id = interface.open_unit.return_value

        pt104 = PT104(interface)
        pt104.connect('tracking')

        assert pt104.is_connected
        pt104.disconnect()

        assert not pt104.is_connected
        interface.close_unit.assert_called_with(id)

    def should_set_mains(self):
        interface = Mock()
        id = interface.open_unit.return_value

        pt104 = PT104(interface)
        pt104.connect('tracking')

        pt104.set_mains(True)

        interface.set_mains.assert_called_with(id, True)

    def should_start_converting(self):
        interface = Mock()
        id = interface.open_unit.return_value

        pt104 = PT104(interface)
        pt104.connect('tracking')

        assert not pt104.is_converting
        pt104.convert()

        interface.convert.assert_called_with(id, pt104.channels)
        assert pt104.is_converting
        for channel in pt104.channels.values():
            assert channel.updated

    def should_get_channel_value(self):
        interface = Mock()
        id = interface.open_unit.return_value

        pt104 = PT104(interface)
        pt104.connect('tracking')

        value = pt104.get_value(1, True)

        assert pt104.is_converting
        assert value == interface.get_value.return_value
        interface.get_value.assert_called_with(id, 1, True)
