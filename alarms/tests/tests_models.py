from django.test import TestCase
from ..models import Alarm, Validity
from cdb.models import Iasio
from .factories import AlarmFactory
from freezegun import freeze_time
import datetime


class AlarmModelTestCase(TestCase):
    """This class defines the test suite for the Alarm model tests"""

    def test_create_alarm(self):
        """Test if we can create an alarm through the models"""
        # Arrange:
        self.old_count = Alarm.objects.count()
        # Act:
        self.alarm = AlarmFactory()
        # Assert:
        self.new_count = Alarm.objects.count()
        self.assertEqual(
            self.old_count + 1,
            self.new_count,
            'The Alarm was not created'
        )
        self.assertEqual(
            Alarm.objects.latest('pk').core_id,
            self.alarm.core_id,
            "The given and saved alarm's core_id differ"
        )

    def test_delete_alarm(self):
        """Test if we can delete an alarm through the models"""
        # Arrange:
        self.alarm = AlarmFactory()
        self.old_count = Alarm.objects.count()
        # Act:
        Alarm.objects.filter(pk=self.alarm.pk).delete()
        # Assert:
        self.new_count = Alarm.objects.count()
        self.assertEqual(
            self.old_count - 1,
            self.new_count,
            'The Alarm was not deleted'
        )

    def test_update_alarm(self):
        """Test if we can update an alarm through the models"""
        # Arrange:
        self.alarm = AlarmFactory()
        # Act:
        new_value = (self.alarm.value + 1) % 2
        self.alarm.value = new_value
        self.alarm.save()
        # Assert:
        self.assertEqual(
            Alarm.objects.get(pk=self.alarm.pk).value,
            new_value,
            'The Alarm was not updated'
        )

    def test_update_alarm_ignoring_timestamp(self):
        """Test if we can update an alarm ignoring changes in the timestamp
        if nothing else is different"""
        # Arrange:
        self.alarm = AlarmFactory()
        # Act:
        new_core_timestamp = self.alarm.core_timestamp + 1000
        same_value = self.alarm.value
        params = {
            'value': same_value,
            'core_timestamp': new_core_timestamp
        }
        self.alarm.update_ignoring_timestamp(params)
        # Assert:
        self.assertNotEqual(
            Alarm.objects.get(pk=self.alarm.pk).core_timestamp,
            new_core_timestamp,
            'Timestamp was changed'
        )

        # Act:
        new_core_timestamp = self.alarm.core_timestamp + 1000
        new_value = (self.alarm.value + 1) % 2
        params = {
            'value': new_value,
            'core_timestamp': new_core_timestamp
        }
        self.alarm.update_ignoring_timestamp(params)
        # Assert:
        self.assertEqual(
            Alarm.objects.get(pk=self.alarm.pk).core_timestamp,
            new_core_timestamp,
            'The alarm timestamp was not updated'
        )
        self.assertEqual(
            Alarm.objects.get(pk=self.alarm.pk).value,
            new_value,
            'The alarm value was not updated'
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
            refresh_rate = Iasio.get_refresh_rate(alarm.core_id)
            validity_delta = Validity.delta()
            max_interval = refresh_rate + validity_delta + 1
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
