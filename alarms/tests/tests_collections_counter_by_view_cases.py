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
        - SET ACK
        - CLEAR ACK
        - CLEAR UNACK

    """

    def set_mock_views_configuration(self, mocker):

        mock_alarms_views_dict = {
            "antenna_alarm_CLEARED": ["antennas"],
            "antenna_alarm_SET_LOW": ["antennas"],
            "antenna_alarm_SET_MEDIUM": ["antennas"],
            "antenna_alarm_SET_HIGH": ["antennas"],
            "antenna_alarm_SET_CRITICAL": ["antennas"],
            "weather_alarm_CLEARED": ["weather"],
            "weather_alarm_SET_LOW": ["weather"],
        }

        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict

    def build_alarms(self):

        mock_alarms = {}

        for core_id, value in [
            ('antenna_alarm_CLEARED', 0),
            ('antenna_alarm_SET_LOW', 1),
            ('antenna_alarm_SET_MEDIUM', 2),
            ('antenna_alarm_SET_HIGH', 3),
            ('antenna_alarm_SET_CRITICAL', 4),
            ('weather_alarm_CLEARED', 0),
            ('weather_alarm_SET_LOW', 1),
        ]:
            alarm = AlarmFactory.build()
            alarm.core_id = core_id
            alarm.views = AlarmCollection.alarms_views_dict.get(
                alarm.core_id, [])
            alarm.value = value
            if value == 0:
                assert alarm.is_set() is False
            else:
                assert alarm.is_set() is True
            assert alarm.ack is False
            mock_alarms[core_id] = alarm

        return mock_alarms

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_counter_by_view_update_for_new_SET_UNACK_alarms(
        self, mocker
    ):
        # Arrange
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset()
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()

        # Initial counter:
        counter = Alarm.objects.counter_by_view()
        assert counter == {}, 'Unexpected count'

        # Act:
        for alarm_key in [
            'antenna_alarm_SET_LOW',
            'antenna_alarm_SET_MEDIUM',
            'antenna_alarm_SET_HIGH',
            'antenna_alarm_SET_CRITICAL',
            'weather_alarm_SET_LOW'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            assert AlarmCollection.get(alarm.core_id).ack is False, """
                Expected unack state
            """
        # Assert:
        expected_counter = {'antennas': 4, 'weather': 1}
        counter = Alarm.objects.counter_by_view()
        assert counter == expected_counter, 'Unexpected count'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_counter_by_view_update_for_new_SET_ACK_alarms(
        self, mocker
    ):
        # Arrange
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset()
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()

        # Initial counter:
        counter = Alarm.objects.counter_by_view()
        assert counter == {}, 'Unexpected count'

        selected_alarm_key = 'antenna_alarm_SET_LOW'
        alarm = mock_alarms_dict[selected_alarm_key]
        alarm.ack = True
        # the system should no allow an ack state for an active alarm
        status = await AlarmCollection.add_or_update_and_notify(alarm)
        assert status == 'created-alarm', \
            'The status must be created-alarm'
        assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
            'New alarms should be created'
        assert AlarmCollection.get(alarm.core_id).ack is False, """
            Expected unack state
        """

        # Transition counter:
        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 1}, 'Unexpected count'

        # Act:
        await AlarmCollection.acknowledge(alarm.core_id)
        assert AlarmCollection.get(alarm.core_id).ack is True, """
            Expected ack state
        """

        # Assert:
        expected_counter = {'antennas': 0}
        counter = Alarm.objects.counter_by_view()
        assert counter == expected_counter, 'Unexpected count'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_counter_by_view_update_for_new_CLEAR_ACK_alarms(
        self, mocker
    ):
        # Arrange
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset()
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()

        # Initial counter:
        counter = Alarm.objects.counter_by_view()
        assert counter == {}, 'Unexpected count'

        # Act:
        for alarm_key in [
            'antenna_alarm_CLEARED',
            'weather_alarm_CLEARED'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            # The system should use an ack state for the new cleared alarms
            # because there are no ack tickets
            assert AlarmCollection.get(alarm.core_id).ack is True, """
                Expected ack state
            """

        # Assert:
        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_counter_by_view_update_for_new_CLEAR_UNACK_alarms(
        self, mocker
    ):
        # Arrange
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset()
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()

        # Initial counter:
        counter = Alarm.objects.counter_by_view()
        assert counter == {}, 'Unexpected count'

        # Act:
        for alarm_key in [
            'antenna_alarm_CLEARED',
            'weather_alarm_CLEARED'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            # The system should use an ack state for the new cleared alarms
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.ack is True, """
                Expected ack state
            """
            AlarmCollection._unacknowledge(stored_alarm)
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.ack is False, """
                Expected unack state
            """

        # Assert:
        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'


class TestCountPerViewForAlarmsUpdates:
    """ This class defines the test suite for the alarms count per view
        after an alarm update

        The update test cases are:
        - SET ACK from and to SET UNACK
        - CLEARED ACK from and to CLEARED UNACK
        - SET ACK from and to CLEAR ACK
        - SET UNACK from and to CLEAR UNACK
        - SET ACK from and to CLEARED UNACK
        - CLEARED ACK from and to SET UNACK

    """

    def set_mock_views_configuration(self, mocker):

        mock_alarms_views_dict = {
            "antenna_alarm_CLEARED": ["antennas"],
            "antenna_alarm_CLEARED_2": ["antennas"],
            "antenna_alarm_SET_LOW": ["antennas"],
            "antenna_alarm_SET_MEDIUM": ["antennas"],
            "antenna_alarm_SET_HIGH": ["antennas"],
            "antenna_alarm_SET_CRITICAL": ["antennas"],
            "weather_alarm_CLEARED": ["weather"],
            "weather_alarm_CLEARED_2": ["weather"],
            "weather_alarm_SET_LOW": ["weather"],
        }

        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict

    def build_alarms(self):

        mock_alarms = {}

        for core_id, value in [
            ('antenna_alarm_CLEARED', 0),
            ('antenna_alarm_CLEARED_2', 0),
            ('antenna_alarm_SET_LOW', 1),
            ('antenna_alarm_SET_MEDIUM', 2),
            ('antenna_alarm_SET_HIGH', 3),
            ('antenna_alarm_SET_CRITICAL', 4),
            ('weather_alarm_CLEARED', 0),
            ('weather_alarm_CLEARED_2', 0),
            ('weather_alarm_SET_LOW', 1),
        ]:
            alarm = AlarmFactory.build()
            alarm.core_id = core_id
            alarm.views = AlarmCollection.alarms_views_dict.get(
                alarm.core_id, [])
            alarm.value = value
            if value == 0:
                assert alarm.is_set() is False
            else:
                assert alarm.is_set() is True
            assert alarm.ack is False
            mock_alarms[core_id] = alarm

        return mock_alarms

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_SET_ACK_from_and_to_SET_UNACK(
        self, mocker
    ):
        # Arrange:
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset()
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()

        #  SET UNACK to SET ACK

        # Initial counter:
        counter = Alarm.objects.counter_by_view()
        assert counter == {}, 'Unexpected count'

        selected_alarm_key = 'antenna_alarm_SET_LOW'

        alarm = mock_alarms_dict[selected_alarm_key]
        alarm.ack = True
        # the system should not allow an ack state for an active alarm
        status = await AlarmCollection.add_or_update_and_notify(alarm)
        assert status == 'created-alarm', \
            'The status must be created-alarm'
        assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
            'New alarms should be created'
        assert AlarmCollection.get(alarm.core_id).ack is False, """
            Expected unack state
        """

        # Transition counter:
        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 1}, 'Unexpected count'

        # Act:
        await AlarmCollection.acknowledge(alarm.core_id)
        stored_alarm = AlarmCollection.get(alarm.core_id)
        assert stored_alarm.ack is True, """
            Expected ack state
        """

        # Assert:
        expected_counter = {'antennas': 0}
        counter = Alarm.objects.counter_by_view()
        assert counter == expected_counter, 'Unexpected count'

        #  SET ACK to SET UNACK

        # Act:
        AlarmCollection._unacknowledge(stored_alarm)
        stored_alarm = AlarmCollection.get(alarm.core_id)
        assert stored_alarm.ack is False, """
            Expected unack state
        """

        # Assert:
        expected_counter = {'antennas': 1}
        counter = Alarm.objects.counter_by_view()
        assert counter == expected_counter, 'Unexpected count'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_CLEARED_ACK_from_and_to_CLEARED_UNACK(
        self, mocker
    ):
        # Arrange:
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset()
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()

        #  CLEARED ACK to CLEARED UNACK

        # Initial counter:
        counter = Alarm.objects.counter_by_view()
        assert counter == {}, 'Unexpected count'

        for alarm_key in [
            'antenna_alarm_CLEARED',
            'weather_alarm_CLEARED'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            # The system should use an ack state for the new cleared alarms
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.ack is True, """
                Expected ack state
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

        # Act:
        for alarm_key in [
            'antenna_alarm_CLEARED',
            'weather_alarm_CLEARED'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.ack is True, """
                Expected ack state
            """
            AlarmCollection._unacknowledge(stored_alarm)
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.ack is False, """
                Expected unack state
            """

        # Assert:
        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

        #  CLEARED UNACK to CLEARED ACK

        # Act:
        for alarm_key in [
            'antenna_alarm_CLEARED',
            'weather_alarm_CLEARED'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.ack is False, """
                Expected unack state
            """
            await AlarmCollection.acknowledge(stored_alarm.core_id)
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.ack is True, """
                Expected ack state
            """

        # Assert:
        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_SET_ACK_from_and_to_CLEAR_ACK(
        self, mocker
    ):
        # Arrange:
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset()
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()

        #  SET ACK to CLEAR ACK

        old_timestamp = int(round(time.time() * 1000))

        for alarm_key in [
            'antenna_alarm_SET_LOW',
            'antenna_alarm_SET_MEDIUM',
            'antenna_alarm_SET_HIGH',
            'antenna_alarm_SET_CRITICAL',
            'weather_alarm_SET_LOW'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            alarm.core_timestamp = old_timestamp
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.is_set() is True, """ Expected set state """
            assert stored_alarm.ack is False, """ Expected unack state """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 4, 'weather': 1}, 'Unexpected count'

        for alarm_key in [
            'antenna_alarm_SET_LOW',
            'antenna_alarm_SET_MEDIUM',
            'antenna_alarm_SET_HIGH',
            'antenna_alarm_SET_CRITICAL',
            'weather_alarm_SET_LOW'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            await AlarmCollection.acknowledge(alarm.core_id)
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.ack is True, """
                Expected ack state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

        new_timestamp = old_timestamp + 10

        for alarm_key in [
            'antenna_alarm_SET_LOW',
            'antenna_alarm_SET_MEDIUM',
            'antenna_alarm_SET_HIGH',
            'antenna_alarm_SET_CRITICAL',
            'weather_alarm_SET_LOW'
        ]:
            alarm = AlarmFactory.build()
            alarm.core_id = mock_alarms_dict[alarm_key].core_id
            alarm.value = 0
            alarm.core_timestamp = new_timestamp
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'updated-alarm', \
                'The status must be updated-alarm'
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.is_set() is False, """
                Expected cleared state
            """
            assert stored_alarm.ack is True, """
                Expected ack state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

        #  CLEAR ACK to SET ACK
        old_timestamp = new_timestamp
        new_timestamp = old_timestamp + 10

        for alarm_key in [
            'antenna_alarm_SET_LOW',
            'antenna_alarm_SET_MEDIUM',
            'antenna_alarm_SET_HIGH',
            'antenna_alarm_SET_CRITICAL',
            'weather_alarm_SET_LOW'
        ]:
            stored_alarm = AlarmCollection.get(
                mock_alarms_dict[alarm_key].core_id
            )
            assert stored_alarm.is_set() is False, """
                Expected cleared state
            """
            assert stored_alarm.ack is True, """
                Expected ack state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """
            alarm = AlarmFactory.build()
            alarm.core_id = mock_alarms_dict[alarm_key].core_id
            alarm.value = 1
            alarm.core_timestamp = new_timestamp
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'updated-alarm', \
                'The status must be updated-alarm'
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.is_set() is True, """
                Expected set state
            """
            assert stored_alarm.ack is False, """
                Expected unack state
            """
            await AlarmCollection.acknowledge(alarm.core_id)
            assert stored_alarm.ack is True, """
                Expected ack state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_SET_UNACK_from_and_to_CLEAR_UNACK(
        self, mocker
    ):
        # Arrange:
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset()
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()

        #  SET UNACK to CLEAR UNACK

        old_timestamp = int(round(time.time() * 1000))

        for alarm_key in [
            'antenna_alarm_SET_LOW',
            'antenna_alarm_SET_MEDIUM',
            'antenna_alarm_SET_HIGH',
            'antenna_alarm_SET_CRITICAL',
            'weather_alarm_SET_LOW'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            alarm.core_timestamp = old_timestamp
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.is_set() is True, """ Expected set state """
            assert stored_alarm.ack is False, """ Expected unack state """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 4, 'weather': 1}, 'Unexpected count'

        new_timestamp = old_timestamp + 10

        for alarm_key in [
            'antenna_alarm_SET_LOW',
            'antenna_alarm_SET_MEDIUM',
            'antenna_alarm_SET_HIGH',
            'antenna_alarm_SET_CRITICAL',
            'weather_alarm_SET_LOW'
        ]:
            alarm = AlarmFactory.build()
            alarm.core_id = mock_alarms_dict[alarm_key].core_id
            alarm.value = 0
            alarm.core_timestamp = new_timestamp
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'updated-alarm', \
                'The status must be updated-alarm'
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.is_set() is False, """
                Expected cleared state
            """
            assert stored_alarm.ack is False, """
                Expected unack state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

        #  CLEAR UNACK to SET UNACK
        old_timestamp = new_timestamp
        new_timestamp = old_timestamp + 10

        for alarm_key in [
            'antenna_alarm_SET_LOW',
            'antenna_alarm_SET_MEDIUM',
            'antenna_alarm_SET_HIGH',
            'antenna_alarm_SET_CRITICAL',
            'weather_alarm_SET_LOW'
        ]:
            stored_alarm = AlarmCollection.get(
                mock_alarms_dict[alarm_key].core_id
            )
            assert stored_alarm.is_set() is False, """
                Expected cleared state
            """
            assert stored_alarm.ack is False, """
                Expected unack state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """
            alarm = AlarmFactory.build()
            alarm.core_id = mock_alarms_dict[alarm_key].core_id
            alarm.value = 1
            alarm.core_timestamp = new_timestamp
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'updated-alarm', \
                'The status must be updated-alarm'
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.is_set() is True, """
                Expected set state
            """
            assert stored_alarm.ack is False, """
                Expected unack state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 4, 'weather': 1}, 'Unexpected count'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_CLEAR_ACK_from_and_to_SET_UNACK(
        self, mocker
    ):
        # Arrange:
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset()
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()

        #  CLEAR_ACK to SET_UNACK

        old_timestamp = int(round(time.time() * 1000))

        # Initial counter:
        counter = Alarm.objects.counter_by_view()
        assert counter == {}, 'Unexpected count'

        for alarm_key in [
            'antenna_alarm_CLEARED',
            'antenna_alarm_CLEARED_2',
            'weather_alarm_CLEARED',
            'weather_alarm_CLEARED_2'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            # The system should use an ack state for the new cleared alarms
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.ack is True, """
                Expected ack state
            """
            assert stored_alarm.is_set() is False, """
                Expected cleared state
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

        new_timestamp = old_timestamp + 10

        for alarm_key in [
            'antenna_alarm_CLEARED',
            'antenna_alarm_CLEARED_2',
            'weather_alarm_CLEARED',
            'weather_alarm_CLEARED_2'
        ]:
            alarm = AlarmFactory.build()
            alarm.core_id = mock_alarms_dict[alarm_key].core_id
            alarm.value = 1
            alarm.core_timestamp = new_timestamp
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'updated-alarm', \
                'The status must be updated-alarm'
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.is_set() is True, """
                Expected set state
            """
            assert stored_alarm.ack is False, """
                Expected unack state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 2, 'weather': 2}, 'Unexpected count'

        #  SET UNACK to CLEAR_ACK
        old_timestamp = new_timestamp
        new_timestamp = old_timestamp + 10

        for alarm_key in [
            'antenna_alarm_CLEARED',
            'antenna_alarm_CLEARED_2',
            'weather_alarm_CLEARED',
            'weather_alarm_CLEARED_2'
        ]:
            stored_alarm = AlarmCollection.get(
                mock_alarms_dict[alarm_key].core_id
            )
            assert stored_alarm.is_set() is True, """
                Expected set state
            """
            assert stored_alarm.ack is False, """
                Expected unack state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """
            alarm = AlarmFactory.build()
            alarm.core_id = mock_alarms_dict[alarm_key].core_id
            alarm.value = 0
            alarm.core_timestamp = new_timestamp
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'updated-alarm', \
                'The status must be updated-alarm'
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.is_set() is False, """
                Expected cleared state
            """
            assert stored_alarm.ack is False, """
                Expected unack state
            """
            await AlarmCollection.acknowledge(alarm.core_id)
            assert stored_alarm.ack is True, """
                Expected ack state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_CLEAR_UNACK_from_and_to_SET_ACK(
        self, mocker
    ):
        # Arrange:
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset()
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()

        #  CLEAR_UNACK to SET_ACK

        old_timestamp = int(round(time.time() * 1000))

        # Initial counter:
        counter = Alarm.objects.counter_by_view()
        assert counter == {}, 'Unexpected count'

        for alarm_key in [
            'antenna_alarm_CLEARED',
            'antenna_alarm_CLEARED_2',
            'weather_alarm_CLEARED',
            'weather_alarm_CLEARED_2'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            # The system should use an ack state for the new cleared alarms
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.ack is True, """
                Expected ack state
            """
            AlarmCollection._unacknowledge(stored_alarm)
            assert stored_alarm.ack is False, """
                Expected unack state
            """
            assert stored_alarm.is_set() is False, """
                Expected cleared state
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

        new_timestamp = old_timestamp + 10

        for alarm_key in [
            'antenna_alarm_CLEARED',
            'antenna_alarm_CLEARED_2',
            'weather_alarm_CLEARED',
            'weather_alarm_CLEARED_2'
        ]:
            alarm = AlarmFactory.build()
            alarm.core_id = mock_alarms_dict[alarm_key].core_id
            alarm.value = 1
            alarm.core_timestamp = new_timestamp
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'updated-alarm', \
                'The status must be updated-alarm'
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.is_set() is True, """
                Expected set state
            """
            assert stored_alarm.ack is False, """
                Expected unack state
            """
            await AlarmCollection.acknowledge(stored_alarm.core_id)
            assert stored_alarm.ack is True, """
                Expected ack state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'

        #  SET ACK to CLEAR_UNACK
        old_timestamp = new_timestamp
        new_timestamp = old_timestamp + 10

        for alarm_key in [
            'antenna_alarm_CLEARED',
            'antenna_alarm_CLEARED_2',
            'weather_alarm_CLEARED',
            'weather_alarm_CLEARED_2'
        ]:
            stored_alarm = AlarmCollection.get(
                mock_alarms_dict[alarm_key].core_id
            )
            assert stored_alarm.is_set() is True, """
                Expected set state
            """
            assert stored_alarm.ack is True, """
                Expected ack state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """
            alarm = AlarmFactory.build()
            alarm.core_id = mock_alarms_dict[alarm_key].core_id
            alarm.value = 0
            alarm.core_timestamp = new_timestamp
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'updated-alarm', \
                'The status must be updated-alarm'
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.is_set() is False, """
                Expected cleared state
            """
            AlarmCollection._unacknowledge(stored_alarm)
            assert stored_alarm.ack is False, """
                Expected unack state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        counter = Alarm.objects.counter_by_view()
        assert counter == {'antennas': 0, 'weather': 0}, 'Unexpected count'


class TestCountByViewForDependencies:
    """ Test suite for selected cases of alarms with dependencies """

    def set_mock_views_configuration(self, mocker):

        mock_alarms_views_dict = {
            "alarm_parent": ["view"],
            "alarm_dependency_one": ["view"],
            "alarm_dependency_two": ["view"],
        }

        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict

    def build_alarms(self):

        mock_alarms = {}

        for core_id, value in [
            ('alarm_parent', 0),
            ('alarm_dependency_one', 0),
            ('alarm_dependency_two', 0)
        ]:
            alarm = AlarmFactory.build()
            alarm.core_id = core_id
            alarm.views = AlarmCollection.alarms_views_dict.get(
                alarm.core_id, [])
            alarm.value = value
            if value == 0:
                assert alarm.is_set() is False
            else:
                assert alarm.is_set() is True
            assert alarm.ack is False
            mock_alarms[core_id] = alarm

        mock_alarms['alarm_parent'].dependencies = [
            mock_alarms['alarm_dependency_one'].core_id,
            mock_alarms['alarm_dependency_two'].core_id
        ]

        return mock_alarms

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_count_for_alarm_parent_with_SET_ACK_to_SET_UNACK_transition(
        self, mocker
    ):

        # Arrange
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset()
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()

        old_timestamp = int(round(time.time() * 1000))

        # Initial counter:
        counter = Alarm.objects.counter_by_view()
        assert counter == {}, 'Unexpected count'

        # Act: Create cleared alarms (order required):
        for alarm_key in [
            'alarm_dependency_one',
            'alarm_dependency_two',
            'alarm_parent'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'created-alarm', \
                'The status must be created-alarm'
            assert alarm.core_id in AlarmCollection.get_all_as_dict(), \
                'New alarms should be created'
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.is_set() is False, """
                Expected cleared state
            """
            # The system should use an ack state for the new cleared alarms
            # because there are no ack tickets
            assert AlarmCollection.get(alarm.core_id).ack is True, """
                Expected ack state
            """

        # Assert:
        counter = Alarm.objects.counter_by_view()
        assert counter == {'view': 0}, 'Unexpected count'

        # Act: Parent and child to set state
        new_timestamp = old_timestamp + 10

        for alarm_key in [
            'alarm_dependency_one',
            'alarm_parent'
        ]:
            alarm = AlarmFactory.build()
            alarm.core_id = mock_alarms_dict[alarm_key].core_id
            alarm.dependencies = mock_alarms_dict[alarm_key].dependencies
            alarm.value = 1
            alarm.core_timestamp = new_timestamp
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'updated-alarm', \
                'The status must be updated-alarm'
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.ack is False, """
                Expected unack state
            """
            assert stored_alarm.is_set() is True, """
                Expected set state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        # Assert:
        counter = Alarm.objects.counter_by_view()
        assert counter == {'view': 2}, 'Unexpected count'

        # Act: Ack child
        for alarm_key in [
            'alarm_dependency_one'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            await AlarmCollection.acknowledge(alarm.core_id)

        for alarm_key in [
            'alarm_dependency_one',
            'alarm_parent'
        ]:
            alarm = mock_alarms_dict[alarm_key]
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.ack is True, """
                Expected ack state
            """
            assert stored_alarm.is_set() is True, """
                Expected set state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        # Assert:
        counter = Alarm.objects.counter_by_view()
        assert counter == {'view': 0}, 'Unexpected count'

        # Act: Other child to set state
        old_timestamp = new_timestamp
        new_timestamp = old_timestamp + 10

        for alarm_key in [
            'alarm_dependency_two'
        ]:
            alarm = AlarmFactory.build()
            alarm.core_id = mock_alarms_dict[alarm_key].core_id
            alarm.dependencies = mock_alarms_dict[alarm_key].dependencies
            alarm.value = 1
            alarm.core_timestamp = new_timestamp
            status = await AlarmCollection.add_or_update_and_notify(alarm)
            assert status == 'updated-alarm', \
                'The status must be updated-alarm'
            stored_alarm = AlarmCollection.get(alarm.core_id)
            assert stored_alarm.ack is False, """
                Expected unack state
            """
            assert stored_alarm.is_set() is True, """
                Expected set state
            """
            assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
                Unexpected views
            """

        alarm_key = 'alarm_parent'
        alarm = mock_alarms_dict[alarm_key]
        stored_alarm = AlarmCollection.get(alarm.core_id)
        assert stored_alarm.ack is False, """
            Expected unack state
        """
        assert stored_alarm.is_set() is True, """
            Expected set state
        """
        assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
            Unexpected views
        """

        alarm_key = 'alarm_dependency_one'
        alarm = mock_alarms_dict[alarm_key]
        stored_alarm = AlarmCollection.get(alarm.core_id)
        assert stored_alarm.ack is True, """
            Expected ack state
        """
        assert stored_alarm.is_set() is True, """
            Expected set state
        """
        assert stored_alarm.views == mock_alarms_dict[alarm_key].views, """
            Unexpected views
        """

        # Assert:
        counter = Alarm.objects.counter_by_view()
        assert counter == {'view': 2}, 'Unexpected count'
