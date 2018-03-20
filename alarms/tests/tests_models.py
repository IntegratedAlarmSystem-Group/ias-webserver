from django.test import TestCase
from ..models import Alarm, Validity, OperationalMode
from .factories import AlarmFactory
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
            alarm.value is 0 or alarm.value is 1
        )
        self.assertTrue(
            type(alarm.core_timestamp) is int
        )
        self.assertTrue(
            alarm.mode in [str(x[0]) for x in OperationalMode.options()]
        )
        self.assertTrue(
            alarm.core_id.startswith("ANTENNA_DV")
            and alarm.core_id.endswith("$WVR$AMBIENT_TEMPERATURE")
        )
        self.assertTrue(
            alarm.running_id == alarm.core_id + '@ACS_NC'
        )
        self.assertTrue(
            alarm.validity in [str(x[0]) for x in Validity.options()]
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
            alarm.validity, '0',
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
            alarm.validity, '1',
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
            max_interval = Validity.refresh_rate() + Validity.delta() + 1
            max_timedelta = datetime.timedelta(milliseconds=max_interval)
            # Act:
            frozen_datetime.tick(delta=max_timedelta)
            alarm.update_validity()
            # Assert:
            self.assertEqual(
                alarm.validity, '0',
                'The validity is not being updated when the alarm is invalid' +
                ' because of an old timestamp'
            )

    def test_equals_except_timestamp(self):
        """Test if we can compare alarms properly through the models"""
        # Arrange:
        self.alarm = AlarmFactory.build()
        self.alarm.value = 0
        self.equal_alarm = Alarm(**self.alarm.to_dict())
        self.different_alarm = Alarm(**self.alarm.to_dict())
        self.different_alarm.value = 1

        # Assert:
        self.assertTrue(
            self.alarm.equals_except_timestamp(self.equal_alarm),
            'Equal alarms are recognized as different'
        )

        self.assertFalse(
            self.alarm.equals_except_timestamp(self.different_alarm),
            'Different alarms are recognized as equal'
        )
