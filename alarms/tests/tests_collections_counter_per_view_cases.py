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

        mock_view_names = ['antennas', 'weather']

        mock_alarms_views_dict = {
            "antenna_alarm_CLEARED": ["antennas"],
            "antenna_alarm_SET_LOW": ["antennas"],
            "antenna_alarm_SET_MEDIUM": ["antennas"],
            "antenna_alarm_SET_HIGH": ["antennas"],
            "antenna_alarm_SET_CRITICAL": ["antennas"],
            "weather_alarm_CLEARED": ["weather"],
            "weather_alarm_SET_LOW": ["weather"],
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
            alarm.value = value
            if value == 0:
                assert alarm.is_set() is False
            else:
                assert alarm.is_set() is True
            mock_alarms[core_id] = alarm

        return mock_alarms

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_counter_by_view_update_for_new_SET_UNACK_alarms(
        self, mocker
    ):
        self.set_mock_views_configuration(mocker)
        mock_alarms_dict = self.build_alarms()

        
