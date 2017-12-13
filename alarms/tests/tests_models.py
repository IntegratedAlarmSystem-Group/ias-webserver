from django.test import TestCase
from ..models import Alarm
from .factories import AlarmFactory


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