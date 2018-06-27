import asyncio
import mock
from django.test import TestCase
from alarms.interfaces import IAlarms
from alarms.collections import AlarmCollection


class TestIAlarm(TestCase):
    """This class defines the test suite for the Alarms Connector"""

    @mock.patch('alarms.collections.AlarmCollection.acknowledge')
    def test_acknowledge_alarms(self, AlarmCollection_acknowledge):
        """
        Test that IAlarm.acknowledge_alarms calls
        AlarmCollection.acknowledge
        """
        # Arrange:
        fake_function = asyncio.Future()
        fake_function.set_result(True)
        AlarmCollection_acknowledge.return_value = fake_function
        core_ids = ['MOCK-ALARM']
        # Act:
        IAlarms.acknowledge_alarms(core_ids)
        # Assert:
        self.assertTrue(
            AlarmCollection_acknowledge.called,
            'The AlarmCollection acknowledge method should have been be called'
        )
        AlarmCollection_acknowledge.assert_called_with(core_ids)

    @mock.patch('alarms.collections.AlarmCollection.shelve')
    def test_shelve_alarms(self, AlarmCollection_shelve):
        """
        Test that IAlarm.shelve_alarm calls
        AlarmCollection.shelve
        """
        # Arrange:
        fake_function = asyncio.Future()
        fake_function.set_result(True)
        AlarmCollection_shelve.return_value = fake_function
        core_id = 'MOCK-ALARM'
        # Act:
        IAlarms.shelve_alarm(core_id)
        # Assert:
        self.assertTrue(
            AlarmCollection_shelve.called,
            'The AlarmCollection shelve method should have been be called'
        )
        AlarmCollection_shelve.assert_called_with(core_id)

    @mock.patch('alarms.collections.AlarmCollection.unshelve')
    def test_unshelve_alarms(self, AlarmCollection_unshelve):
        """
        Test that IAlarm.unshelve_alarms calls
        AlarmCollection.unshelve
        """
        # Arrange:
        fake_function = asyncio.Future()
        fake_function.set_result(True)
        AlarmCollection_unshelve.return_value = fake_function
        core_ids = ['MOCK-ALARM']
        # Act:
        IAlarms.unshelve_alarms(core_ids)
        # Assert:
        self.assertTrue(
            AlarmCollection_unshelve.called,
            'The AlarmCollection unshelve method should have been be called'
        )
        AlarmCollection_unshelve.assert_called_with(core_ids)

    @mock.patch(
        'alarms.collections.AlarmCollection.get_dependencies_recursively',
        return_value=['MOCK-ALARM', 'MOCK-ALARM-DEPENDENCY'])
    def test_get_alarm_dependencies(
        self, AlarmCollection_get_dependencies_recursively
    ):
        """
        Test that IAlarm.get_alarm_dependencies calls
        AlarmCollection.get_dependencies_recursively
        """
        # Arrange:
        core_id = 'MOCK-ALARM'
        # Act:
        IAlarms.get_alarm_dependencies(core_id)
        # Assert:
        self.assertTrue(
            AlarmCollection_get_dependencies_recursively.called,
            'The AlarmCollection get dependencies recursively method should \
            have been be called'
        )
        AlarmCollection_get_dependencies_recursively.assert_called_with(
            core_id
        )
