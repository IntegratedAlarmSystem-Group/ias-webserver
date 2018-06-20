import pytest
from pytest_mock import mocker
from tickets.connectors import AlarmConnector
from alarms.interfaces import IAlarms


class TestAlarmConnector:
    """This class defines the test suite for the Alarms Connector"""

    def test_acknowledge_alarms(self, mocker):
        """
        Test that AlarmConnector.acknowledge_alarms calls
        IAlarms.acknowledge_alarms
        """
        # Arrange:
        # Mock IAlarms.acknowledge_alarms to assert if it was called
        # and avoid calling the real function
        mocker.patch.object(IAlarms, 'acknowledge_alarms')
        core_ids = ['MOCK-ALARM']
        # Act:
        AlarmConnector.acknowledge_alarms(core_ids)
        # Assert:
        assert IAlarms.acknowledge_alarms.call_count == 1, \
            'The IAlarms.acknowledge_alarms function was not called'
        IAlarms.acknowledge_alarms.assert_called_with(core_ids)

    def test_shelve_alarm(self, mocker):
        """
        Test that AlarmConnector.shelve_alarm calls
        IAlarm.shelve_alarm
        """
        # Arrange:
        # Mock AlarmCollection.shelve to assert if it was called
        # and avoid calling the real function
        mocker.patch.object(IAlarms, 'shelve_alarm')
        core_id = 'MOCK-ALARM'
        # Act:
        AlarmConnector.shelve_alarm(core_id)
        # Assert:
        assert IAlarms.shelve_alarm.call_count == 1, \
            'The IAlarms.shelve_alarm function was not called'
        IAlarms.shelve_alarm.assert_called_with(core_id)

    def test_unshelve_alarms(self, mocker):
        """
        Test that AlarmConnector.unshelve_alarm calls
        IAlarm.unshelve_alarms
        """
        # Arrange:
        # Mock AlarmCollection.unshelve to assert if it was called
        # and avoid calling the real function
        mocker.patch.object(IAlarms, 'unshelve_alarms')
        core_ids = ['MOCK-ALARM']
        # Act:
        AlarmConnector.unshelve_alarms(core_ids)
        # Assert:
        assert IAlarms.unshelve_alarms.call_count == 1, \
            'The IAlarms.unshelve_alarms function was not called'
        IAlarms.unshelve_alarms.assert_called_with(core_ids)
