import datetime
import time
import pytest
from freezegun import freeze_time
from alarms.models import Alarm, Value, IASValue
from alarms.tests.factories import AlarmFactory
from alarms.collections import AlarmCollection
from alarms.connectors import PanelsConnector


class TestCountByViewForNewAlarms:
    """ This class defines the test suite for the alarms count by view
        for new alarms

        The update test cases are new alarms for the following cases:
        - SET UNACK
        - CLEARED
        - SET ACK

    """

    def create_alarm(self, core_id, **kwargs):
        value = kwargs.get('value', Value.CLEARED).value
        alarm = Alarm(
            value=value,
            mode=7,
            validity=0,
            core_timestamp=10000,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        return alarm

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_counter_by_view_update_for_new_SET_UNACK_alarms(
        self, mocker
    ):

        # Arrange:
        mock_view_names = ['antennas', 'weather']

        mock_alarms_views_dict = {
            "antenna_alarm_0": ["antennas"],
            "antenna_alarm_1": ["antennas"],
            "antenna_alarm_2": ["antennas"],
            "antenna_alarm_3": ["antennas"],
            "weather_alarm_0": ["weather"],
        }

        PanelsConnector_get_names_of_views = \
            mocker.patch.object(
                PanelsConnector, 'get_names_of_views'
            )
        PanelsConnector_get_names_of_views.return_value = mock_view_names

        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict

        # Alarms:
        mock_alarms = []

        for core_id, value in [
            ('antenna_alarm_0', Value.SET_LOW),
            ('antenna_alarm_1', Value.SET_MEDIUM),
            ('antenna_alarm_2', Value.SET_CRITICAL),
            ('antenna_alarm_3', Value.SET_HIGH),
            ('weather_alarm_0', Value.SET_LOW),
        ]:
            alarm = self.create_alarm(core_id, value=value)
            assert alarm.ack is not True, 'Expected unack state'
            mock_alarms.append(alarm)

        AlarmCollection.reset()

        # Initial counter:
        counter = AlarmCollection.counter_by_view
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

        # Act:
        for alarm in mock_alarms:
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            assert alarm.ack is not True, 'Expected unack state'

        # Assert:
        expected_counter = {'antennas': 4, 'weather': 1}
        counter = AlarmCollection.counter_by_view
        assert counter == expected_counter, 'Unexpected count'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_counter_by_view_cannot_change_for_new_CLEARED_alarms(
        self, mocker
    ):

        # Arrange:
        mock_view_names = ['antennas', 'weather']

        mock_alarms_views_dict = {
            "antenna_alarm_0": ["antennas"],
            "antenna_alarm_1": ["antennas"],
            "weather_alarm_0": ["weather"],
        }

        PanelsConnector_get_names_of_views = \
            mocker.patch.object(
                PanelsConnector, 'get_names_of_views'
            )
        PanelsConnector_get_names_of_views.return_value = mock_view_names

        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict

        AlarmCollection.reset()

        # Arrange: Alarms at the start:
        mock_alarms_start = []
        for core_id, value in [
            ('antenna_alarm_0', Value.SET_LOW),
        ]:
            alarm = self.create_alarm(core_id, value=value)
            assert alarm.ack is not True, 'Expected unack state'
            mock_alarms_start.append(alarm)

        for alarm in mock_alarms_start:
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            assert alarm.ack is not True, 'Expected unack state'

        # Arrange: Initial counter:
        counter = AlarmCollection.counter_by_view
        assert counter == {'antennas': 1, 'weather': 0}, 'Unexpected count'

        # Arrange: New cleared alarms
        mock_alarms = []  # new list of alarms
        for core_id, value in [
            ('antenna_alarm_1', Value.CLEARED),
            ('weather_alarm_0', Value.CLEARED),
        ]:
            alarm = self.create_alarm(core_id, value=value)
            mock_alarms.append(alarm)

        # Act:
        for alarm in mock_alarms:
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'

        # Assert:
        expected_counter = {'antennas': 1, 'weather': 0}
        counter = AlarmCollection.counter_by_view
        assert counter == expected_counter, 'Unexpected count'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_counter_by_view_cannot_change_for_new_SET_ACK_alarms(
        self, mocker
    ):

        # Arrange:
        mock_view_names = ['antennas', 'weather']

        mock_alarms_views_dict = {
            "antenna_alarm_0": ["antennas"],
            "antenna_alarm_1": ["antennas"],
            "weather_alarm_0": ["weather"],
        }

        PanelsConnector_get_names_of_views = \
            mocker.patch.object(
                PanelsConnector, 'get_names_of_views'
            )
        PanelsConnector_get_names_of_views.return_value = mock_view_names

        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict

        AlarmCollection.reset()

        # Arrange: Alarms at the start:
        mock_alarms_start = []
        for core_id, value in [
            ('antenna_alarm_0', Value.SET_LOW),
        ]:
            alarm = self.create_alarm(core_id, value=value)
            assert alarm.ack is not True, 'Expected unack state'
            mock_alarms_start.append(alarm)

        for alarm in mock_alarms_start:
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            assert alarm.ack is not True, 'Expected unack state'

        # Arrange: Initial counter:
        counter = AlarmCollection.counter_by_view
        assert counter == {'antennas': 1, 'weather': 0}, 'Unexpected count'

        # Arrange: New set alarms
        mock_alarms = []  # new list of alarms
        for core_id, value in [
            ('antenna_alarm_1', Value.SET_LOW),
            ('weather_alarm_0', Value.SET_LOW),
        ]:
            alarm = self.create_alarm(core_id, value=value)
            assert alarm.ack is not True, 'Expected unack state'
            mock_alarms.append(alarm)

        # Act: New alarms with set state
        for alarm in mock_alarms:
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'

        # Transition counter
        counter = AlarmCollection.counter_by_view
        assert counter == {'antennas': 2, 'weather': 1}, 'Unexpected count'

        # Act: Acknowledge alarms
        for alarm in mock_alarms:
            await AlarmCollection.acknowledge(alarm.core_id)

        for alarm in mock_alarms:
            assert alarm.ack is True, 'Expected ack state'

        # Assert:
        expected_counter = {'antennas': 1, 'weather': 0}
        counter = AlarmCollection.counter_by_view
        assert counter == expected_counter, 'Unexpected count'


class TestCountPerViewForAlarmsUpdates:
    """ This class defines the test suite for the alarms count per view
        after an alarm update

        The update test cases are:
        - CLEARED to SET UNACK
        - SET UNACK to SET ACK
        - SET UNACK to CLEAR
        - SET ACK to CLEAR

    """

    def create_alarm(self, core_id, **kwargs):
        value = kwargs.get('value', Value.CLEARED).value
        timestamp = kwargs.get('timestamp', int(round(time.time() * 1000)))
        ack = kwargs.get('ack', False)
        alarm = Alarm(
            value=value,
            mode=7,
            validity=0,
            core_timestamp=timestamp,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        alarm.ack = ack
        return alarm

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_counter_by_view_update_CLEAR_to_SET_UNACK(
        self, mocker
    ):

        # Arrange:
        mock_view_names = ['antennas', 'weather']

        mock_alarms_views_dict = {
            "antenna_alarm_0": ["antennas"],
            "weather_alarm_0": ["weather"],
        }

        PanelsConnector_get_names_of_views = \
            mocker.patch.object(
                PanelsConnector, 'get_names_of_views'
            )
        PanelsConnector_get_names_of_views.return_value = mock_view_names

        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict

        AlarmCollection.reset()

        # Arrange: Alarms at the start:
        old_timestamp = int(round(time.time() * 1000))
        mock_alarms_start = []
        for core_id, value, timestamp in [
            ('antenna_alarm_0', Value.CLEARED, old_timestamp),
            ('weather_alarm_0', Value.CLEARED, old_timestamp),
        ]:
            alarm = self.create_alarm(
                core_id, value=value, timestamp=timestamp)
            mock_alarms_start.append(alarm)

        for alarm in mock_alarms_start:
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'

        # Arrange: Initial counter:
        counter = AlarmCollection.counter_by_view
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

        # Act: Update to set unack
        new_timestamp = old_timestamp + 10
        mock_alarms = []  # new list of alarms
        for core_id, value, timestamp in [
            ('antenna_alarm_0', Value.SET_LOW, new_timestamp),
            ('weather_alarm_0', Value.SET_LOW, new_timestamp),
        ]:
            alarm = self.create_alarm(
                core_id, value=value, timestamp=timestamp)
            assert alarm.ack is not True, 'Expected unack state'
            mock_alarms.append(alarm)

        for alarm in mock_alarms:
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'updated-alarm', \
                'The status must be updated-alarm'
            assert alarm.ack is not True, 'Expected unack state'

        # Assert:
        expected_counter = {'antennas': 1, 'weather': 1}
        counter = AlarmCollection.counter_by_view
        assert counter == expected_counter, \
            'Unexpected count for the CLEAR to SET UNACK case'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_counter_by_view_update_SET_UNACK_to_SET_ACK(
        self, mocker
    ):

        # Arrange:
        mock_view_names = ['antennas', 'weather']

        mock_alarms_views_dict = {
            "antenna_alarm_0": ["antennas"],
            "weather_alarm_0": ["weather"],
        }

        PanelsConnector_get_names_of_views = \
            mocker.patch.object(
                PanelsConnector, 'get_names_of_views'
            )
        PanelsConnector_get_names_of_views.return_value = mock_view_names

        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict

        AlarmCollection.reset()

        # Arrange: Alarms at the start:
        old_timestamp = int(round(time.time() * 1000))
        mock_alarms = []
        for core_id, value, timestamp in [
            ('antenna_alarm_0', Value.SET_LOW, old_timestamp),
            ('weather_alarm_0', Value.SET_LOW, old_timestamp),
        ]:
            alarm = self.create_alarm(
                core_id, value=value, timestamp=timestamp)
            assert alarm.ack is not True, 'Expected unack state'
            mock_alarms.append(alarm)

        for alarm in mock_alarms:
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            assert alarm.ack is not True, 'Expected unack state'

        # Arrange: Initial counter:
        counter = AlarmCollection.counter_by_view
        assert counter == {'antennas': 1, 'weather': 1}, 'Unexpected count'

        # Act: 'Update' to set ack
        for alarm in mock_alarms:
            await AlarmCollection.acknowledge(alarm.core_id)

        for alarm in mock_alarms:
            assert alarm.ack is True, 'Expected ack state'

        # Assert:
        expected_counter = {'antennas': 0, 'weather': 0}
        counter = AlarmCollection.counter_by_view
        assert counter == expected_counter, \
            'Unexpected count for the SET UNACK to SET ACK case'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_counter_by_view_update_SET_UNACK_to_CLEARED(
        self, mocker
    ):

        # Arrange:
        mock_view_names = ['antennas', 'weather']

        mock_alarms_views_dict = {
            "antenna_alarm_0": ["antennas"],
            "weather_alarm_0": ["weather"],
        }

        PanelsConnector_get_names_of_views = \
            mocker.patch.object(
                PanelsConnector, 'get_names_of_views'
            )
        PanelsConnector_get_names_of_views.return_value = mock_view_names

        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict

        AlarmCollection.reset()

        # Arrange: Alarms at the start:
        old_timestamp = int(round(time.time() * 1000))
        mock_alarms_start = []
        for core_id, value, timestamp in [
            ('antenna_alarm_0', Value.SET_LOW, old_timestamp),
            ('weather_alarm_0', Value.SET_LOW, old_timestamp),
        ]:
            alarm = self.create_alarm(
                core_id, value=value, timestamp=timestamp)

            mock_alarms_start.append(alarm)

        for alarm in mock_alarms_start:
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            assert alarm.ack is not True, 'Expected unack state'

        # Arrange: Initial counter:
        counter = AlarmCollection.counter_by_view
        assert counter == {'antennas': 1, 'weather': 1}, 'Unexpected count'

        # Act: Update to set unack
        new_timestamp = old_timestamp + 10
        mock_alarms = []  # new list of alarms
        for core_id, value, timestamp in [
            ('antenna_alarm_0', Value.CLEARED, new_timestamp),
            ('weather_alarm_0', Value.CLEARED, new_timestamp),
        ]:
            alarm = self.create_alarm(
                core_id, value=value, timestamp=timestamp)
            mock_alarms.append(alarm)

        for alarm in mock_alarms:
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'updated-alarm', \
                'The status must be updated-alarm'
        # Assert:
        expected_counter = {'antennas': 0, 'weather': 0}
        counter = AlarmCollection.counter_by_view
        assert counter == expected_counter, \
            'Unexpected count for the SET UNACK to CLEARED case'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_counter_by_view_update_SET_ACK_to_CLEARED(
        self, mocker
    ):

        # Arrange:
        mock_view_names = ['antennas', 'weather']

        mock_alarms_views_dict = {
            "antenna_alarm_0": ["antennas"],
            "antenna_alarm_1": ["antennas"],
            "weather_alarm_0": ["weather"],
        }

        PanelsConnector_get_names_of_views = \
            mocker.patch.object(
                PanelsConnector, 'get_names_of_views'
            )
        PanelsConnector_get_names_of_views.return_value = mock_view_names

        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict

        AlarmCollection.reset()

        # Arrange: Alarms at the start:
        old_timestamp = int(round(time.time() * 1000))
        mock_alarms_start = []
        for core_id, value, timestamp in [
            ('antenna_alarm_0', Value.SET_LOW, old_timestamp),
            ('antenna_alarm_1', Value.SET_LOW, old_timestamp),
            ('weather_alarm_0', Value.SET_LOW, old_timestamp),
        ]:
            alarm = self.create_alarm(
                core_id, value=value, timestamp=timestamp)
            mock_alarms_start.append(alarm)

        for alarm in mock_alarms_start:
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            assert alarm.ack is not True, 'Expected unack state'

        # Arrange: Acknowledge alarms to have a 'set ack' status'
        for alarm in mock_alarms_start:
            await AlarmCollection.acknowledge(alarm.core_id)

        for alarm in mock_alarms_start:
            assert alarm.ack is True, 'Expected ack state'

        # Arrange: Initial counter:
        counter = AlarmCollection.counter_by_view
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

        # Act: Update to cleared
        new_timestamp = old_timestamp + 10
        mock_alarms = []  # new list of alarms
        for core_id, value, timestamp, ack in [
            ('antenna_alarm_0', Value.CLEARED, new_timestamp, True),
            ('antenna_alarm_1', Value.CLEARED, new_timestamp, True),
            ('weather_alarm_0', Value.CLEARED, new_timestamp, True),
        ]:
            alarm = self.create_alarm(
                core_id, value=value, timestamp=timestamp, ack=ack)
            mock_alarms.append(alarm)

        for alarm in mock_alarms:
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'updated-alarm', \
                'The status must be updated-alarm'
        # Assert:
        expected_counter = {'antennas': 0, 'weather': 0}
        counter = AlarmCollection.counter_by_view
        assert counter == expected_counter, \
            'Unexpected count for the SET ACK to CLEARED case'
