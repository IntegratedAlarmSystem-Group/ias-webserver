import copy
import datetime
from freezegun import freeze_time
from django.test import TestCase
from alarms.models import Alarm, Validity, OperationalMode, Value
from alarms.connectors import CdbConnector as CdbConn
from alarms.tests.factories import AlarmFactory


class AlarmModelTestCase(TestCase):
    """This class defines the test suite for the Alarm model tests"""

    def test_alarm_factory(self):
        """Test if the alarm factory is creating alarms as expected"""
        # Act:
        alarm = AlarmFactory.build()
        # Assert:
        self.assertTrue(
            alarm.value in [int(x[0]) for x in Value.options()],
            'The value is not a valid option'
        )
        self.assertTrue(
            type(alarm.core_timestamp) is int,
            'The core_timestamp is not of type int'
        )
        self.assertTrue(
            type(alarm.state_change_timestamp) is int,
            'The state_change_timestamp is not of type int'
        )
        self.assertTrue(
            alarm.mode in [int(x[0]) for x in OperationalMode.options()],
            'The mode is not a valid option'
        )
        self.assertTrue(
            type(alarm.core_id) is str,
            'The core_id is not a string'
        )
        self.assertTrue(
            '@' not in alarm.core_id and ':' not in alarm.core_id,
            'The core_id contains an invalid character (@ or :)'
        )
        self.assertTrue(
            alarm.running_id == alarm.core_id + '@ACS_NC',
            'The running_id has an unexpected value'
        )
        self.assertTrue(
            alarm.validity in [int(x[0]) for x in Validity.options()],
            'The validity is not a valid option'
        )
        self.assertTrue(
            alarm.timestamps == {},
            'The default value of timestamps field must be an empty dictionary'
        )
        self.assertTrue(
            alarm.properties == {},
            'The default value of properties field must be an empty dictionary'
        )
        self.assertTrue(
            alarm.dependencies == [],
            'The default value of dependencies field must be an empty list'
        )
        self.assertEqual(
            alarm.ack, False,
            'The default value of ack field must be False'
        )

    def test_update_alarm_value(self):
        """ Test that an Alarm value can be updated and its
        state_change_timestamp is updated accordingly """
        # Arrange:
        alarm = AlarmFactory.build()
        alarm.value = 0
        new_alarm = copy.deepcopy(alarm)
        new_alarm.core_timestamp = alarm.core_timestamp + 10
        new_alarm.value = 1
        expected_data = dict(new_alarm.to_dict())
        old_state_change = alarm.state_change_timestamp
        # Act:
        alarm.update(new_alarm)
        # Assert:
        new_state_change = alarm.state_change_timestamp
        updated_data = dict(alarm.to_dict())
        expected_state_change = expected_data['state_change_timestamp']
        del updated_data['state_change_timestamp']
        del expected_data['state_change_timestamp']
        self.assertEqual(
            updated_data, expected_data,
            'The Alarm was not updated correctly'
        )
        self.assertTrue(
            old_state_change < new_state_change,
            'The Alarm state_change_timestamp should have been updated'
        )
        self.assertEqual(
            new_state_change, alarm.core_timestamp,
            'The Alarm state_change_timestamp should have been updated'
        )

    def test_update_alarm_mode(self):
        """ Test that an Alarm mode can be updated and its
        state_change_timestamp is updated accordingly """
        # Arrange:
        alarm = AlarmFactory.build()
        alarm.mode = 0
        new_alarm = copy.deepcopy(alarm)
        new_alarm.core_timestamp = alarm.core_timestamp + 10
        new_alarm.mode = 1
        expected_data = dict(new_alarm.to_dict())
        old_state_change = alarm.state_change_timestamp
        # Act:
        alarm.update(new_alarm)
        # Assert:
        new_state_change = alarm.state_change_timestamp
        updated_data = dict(alarm.to_dict())
        expected_state_change = expected_data['state_change_timestamp']
        del updated_data['state_change_timestamp']
        del expected_data['state_change_timestamp']
        self.assertEqual(
            updated_data, expected_data,
            'The Alarm was not updated correctly'
        )
        self.assertTrue(
            old_state_change < new_state_change,
            'The state_change_timestamp should have increased'
        )
        self.assertEqual(
            new_state_change, alarm.core_timestamp,
            'The state_change_timestamp should be equal to the core_timestamp'
        )

    def test_update_alarm_validity(self):
        """ Test that an Alarm validity can be updated and its
        state_change_timestamp stays unchanged """
        # Arrange:
        alarm = AlarmFactory.build()
        alarm.validity = 0
        new_alarm = copy.deepcopy(alarm)
        new_alarm.core_timestamp = alarm.core_timestamp + 10
        new_alarm.validity = 1
        expected_data = dict(new_alarm.to_dict())
        old_state_change = alarm.state_change_timestamp
        # Act:
        alarm.update(new_alarm)
        # Assert:
        new_state_change = alarm.state_change_timestamp
        updated_data = dict(alarm.to_dict())
        expected_state_change = expected_data['state_change_timestamp']
        del updated_data['state_change_timestamp']
        del expected_data['state_change_timestamp']
        self.assertEqual(
            updated_data, expected_data,
            'The Alarm was not updated correctly'
        )
        self.assertEqual(
            old_state_change, new_state_change,
            'The state_change_timestamp should not have changed'
        )
        self.assertTrue(
            new_state_change < alarm.core_timestamp,
            'state_change_timestamp should not be updated to core_timestamp'
        )

    def test_ignored_invalid_alarms_update(self):
        """ Test if the UNREALIABLE alarm keep the validity as UNREALIABLE
        even if the validity is recalculated before the valid refresh time
        elapsed """
        # Arrange:
        alarm = AlarmFactory.get_invalid_alarm()
        # Act:
        alarm.update_validity()
        # Assert:
        self.assertEqual(
            alarm.validity, 0,
            'The validity must keep it UNREALIABLE even if the ' +
            'core_timestamp is current'
        )

    def test_ignored_valid_alarm_update(self):
        """ Test if a RELIABLE alarm keep the validity as RELIABLE if the
        validity is recalculated before the valid refresh time elapsed """
        # Arrange:
        alarm = AlarmFactory.get_valid_alarm()
        # Act:
        alarm.update_validity()
        # Assert:
        self.assertEqual(
            alarm.validity, 1,
            'The validity must keep it REALIABLE if the ' +
            'core_timestamp is current'
        )

    def test_updated_invalid_alarms(self):
        """ Test if the alarm validity is changed to UNREALIABLE when the
        elapsed time is greater than the refresh rate considering a margin
        error
        """
        initial_time = datetime.datetime.now()
        with freeze_time(initial_time) as frozen_datetime:
            # Arrange:
            alarm = AlarmFactory.get_valid_alarm()
            max_interval = CdbConn.refresh_rate + CdbConn.tolerance + 1
            max_timedelta = datetime.timedelta(milliseconds=max_interval)
            # Act:
            frozen_datetime.tick(delta=max_timedelta)
            alarm.update_validity()
            # Assert:
            self.assertEqual(
                alarm.validity, 0,
                'The validity is not being updated when the alarm is invalid' +
                ' because of an old timestamp'
            )

    def test_equals_except_timestamp(self):
        """Test if we can compare alarms properly through the models"""
        # Arrange:
        self.alarm = AlarmFactory.get_alarm_with_all_optional_fields()

        self.alarm.value = 0
        self.equal_alarm = Alarm(**self.alarm.to_dict())

        self.equal_alarm_diff_tstamp = Alarm(**self.alarm.to_dict())
        self.equal_alarm_diff_tstamp.timestamps = {"sentToBsdbTStamp": "0"}

        self.different_alarm = Alarm(**self.alarm.to_dict())
        self.different_alarm.value = 1

        # Assert:
        self.assertTrue(
            self.alarm.equals_except_timestamp(self.equal_alarm),
            'Equal alarms are recognized as different'
        )

        self.assertTrue(
            self.alarm.equals_except_timestamp(self.equal_alarm_diff_tstamp),
            'Equal alarms with different tstamps are recognized as different'
        )

        self.assertFalse(
            self.alarm.equals_except_timestamp(self.different_alarm),
            'Different alarms are recognized as equal'
        )

    def test_acknowledge_set_alarms(self):
        """ Test if a SET alarm can be acknowledged """
        # Arrange:
        alarm = AlarmFactory.build()
        alarm.ack = False
        alarm.value = 1
        # Act:
        alarm.acknowledge()
        # Assert:
        self.assertEquals(
            alarm.ack, True, 'A SET Alarm could not be acknowledged'
        )

    def test_acknowledge_clear_alarms(self):
        """ Test if a CLEAR alarm can be acknowledged """
        # Arrange:
        alarm = AlarmFactory.build()
        alarm.ack = False
        alarm.value = 0
        # Act:
        alarm.acknowledge()
        # Assert:
        self.assertEquals(
            alarm.ack, True, 'A CLEAR Alarm could not be acknowledged'
        )

    def test_shelve_alarm(self):
        """ Test if an alarm can be shelved """
        # Arrange:
        alarm = AlarmFactory.build()
        # Act:
        alarm.shelve()
        # Assert:
        self.assertEquals(
            alarm.shelved, True, 'The Alarm was not shelved'
        )

    def test_unshelve_alarm(self):
        """ Test if an alarm can be unshelved """
        # Arrange:
        alarm = AlarmFactory.build()
        alarm.shelve()
        # Act:
        alarm.unshelve()
        # Assert:
        self.assertEquals(
            alarm.shelved, False, 'The Alarm was not unshelved'
        )
