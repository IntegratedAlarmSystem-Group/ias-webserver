import mock
from django.test import TestCase
from tickets.connectors import AlarmConnector
from alarms.interfaces import IAlarms


class TestAlarmConnector(TestCase):
    """This class defines the test suite for the Alarms Connector"""

    @mock.patch('alarms.interfaces.IAlarms.acknowledge_alarms')
    def test_acknowledge_alarms(self, IAlarms_acknowledge_alarms):
        """
        Test that AlarmConnector.acknowledge_alarms calls
        IAlarms.acknowledge_alarms
        """
        # Arrange:
        core_ids = ['MOCK-ALARM']
        IAlarms_acknowledge_alarms.return_value = core_ids
        # Act:
        ack_alarms_ids = AlarmConnector.acknowledge_alarms(core_ids)
        # Assert:
        self.assertTrue(
            IAlarms_acknowledge_alarms.called,
            'The IAlarms.acknowledge_alarms function was not called'
        )
        IAlarms_acknowledge_alarms.assert_called_with(core_ids)
        self.assertEqual(
            ack_alarms_ids, core_ids,
            'The IAlarm acknowledge method should return a list of \
            acknowledged alarms'
        )

    @mock.patch('alarms.interfaces.IAlarms.shelve_alarm')
    def test_shelve_alarm(self, IAlarms_shelve_alarm):
        """
        Test that AlarmConnector.shelve_alarm calls
        IAlarms.shelve_alarm
        """
        # Arrange:
        core_id = 'MOCK-ALARM'
        # Act:
        AlarmConnector.shelve_alarm(core_id)
        # Assert:
        self.assertTrue(
            IAlarms_shelve_alarm.called,
            'The IAlarms.shelve_alarm function was not called'
        )
        IAlarms_shelve_alarm.assert_called_with(core_id)

    @mock.patch('alarms.interfaces.IAlarms.unshelve_alarms')
    def test_unshelve_alarms(self, IAlarms_unshelve_alarms):
        """
        Test that AlarmConnector.unshelve_alarms calls
        IAlarms.unshelve_alarms
        """
        # Arrange:
        core_ids = ['MOCK-ALARM']
        # Act:
        AlarmConnector.unshelve_alarms(core_ids)
        # Assert:
        self.assertTrue(
            IAlarms_unshelve_alarms.called,
            'The IAlarms.unshelve_alarms function was not called'
        )
        IAlarms_unshelve_alarms.assert_called_with(core_ids)

    @mock.patch('alarms.interfaces.IAlarms.get_alarm_dependencies')
    def test_get_alarm_dependencies(self, IAlarms_get_alarm_dependencies):
        """
        Test that AlarmConnector.get_alarm_dependencies calls
        IAlarms.get_alarm_dependencies
        """
        # Arrange:
        core_ids = ['MOCK-ALARM']
        # Act:
        AlarmConnector.get_alarm_dependencies(core_ids)
        # Assert:
        self.assertTrue(
            IAlarms_get_alarm_dependencies.called,
            'The IAlarms.get_alarm_dependencies function was not called'
        )
        IAlarms_get_alarm_dependencies.assert_called_with(core_ids)

    @mock.patch('alarms.interfaces.IAlarms.get_alarm_ancestors')
    def test_get_alarm_ancestors(self, IAlarms_get_alarm_ancestors):
        """
        Test that AlarmConnector.get_alarm_ancestors calls
        IAlarms.get_alarm_ancestors
        """
        # Arrange:
        core_ids = ['MOCK-ALARM']
        # Act:
        AlarmConnector.get_alarm_ancestors(core_ids)
        # Assert:
        self.assertTrue(
            IAlarms_get_alarm_ancestors.called,
            'The IAlarms.get_alarm_ancestors function was not called'
        )
        IAlarms_get_alarm_ancestors.assert_called_with(core_ids)
