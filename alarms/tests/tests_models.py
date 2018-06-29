from django.test import TestCase
from alarms.models import Alarm, Validity, OperationalMode, Value
from alarms.connectors import CdbConnector as CdbConn
from alarms.tests.factories import AlarmFactory
from freezegun import freeze_time
import datetime


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
