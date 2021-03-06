from datetime import timedelta
from freezegun import freeze_time
from django.test import TestCase
from django.utils import timezone
from tickets.models import ShelveRegistry, ShelveRegistryStatus


class ShelveRegistryModelsTestCase(TestCase):
    """This class defines the test suite for the ShelveRegistry model tests"""

    def setUp(self):
        self.alarm_id = 'alarm_id'
        self.message = 'Shelving because of reasons'
        self.user = 'testuser'

    def test_create_registry(self):
        """ Test if we can create a shelve_registry"""
        resolution_dt = timezone.now()
        with freeze_time(resolution_dt):
            # Act:
            registry = ShelveRegistry(
                alarm_id=self.alarm_id, message=self.message, user=self.user
            )
            registry.save()
            retrieved_reg = ShelveRegistry.objects.get(alarm_id=self.alarm_id)

        # Asserts:
        self.assertEqual(
            retrieved_reg.status,
            int(ShelveRegistryStatus.get_choices_by_name()['SHELVED']),
            'Registry must be shelved by default'
        )
        self.assertEqual(
            retrieved_reg.shelved_at, resolution_dt,
            'Registry was not created with the correct shelved timestamp'
        )
        self.assertEqual(
            retrieved_reg.unshelved_at, None,
            'When the registry is created the unshelved time must be none'
        )
        self.assertEqual(
            retrieved_reg.message, self.message,
            'When the registry is created the message must not be none'
        )
        self.assertEqual(
            retrieved_reg.timeout, timedelta(hours=12),
            'The default timeout should be 12 hours'
        )
        self.assertEqual(
            retrieved_reg.user, self.user,
            'When the registry is created the message must not be none'
        )

    def test_cannot_create_registry_with_no_message(self):
        """ Test if we cannot create a shelve_registry without a message"""
        # Act:
        registry = ShelveRegistry(alarm_id=self.alarm_id)
        with self.assertRaises(ValueError):
            registry.save()

    def test_unshelve_a_registry(self):
        """ Test if we can unshelve an alarm """
        # Arrange:
        registry = ShelveRegistry(
            alarm_id=self.alarm_id, message=self.message, user=self.user
        )
        registry.save()

        # Act:
        resolution_dt = timezone.now()
        with freeze_time(resolution_dt):
            response = registry.unshelve()
            retrieved_reg = ShelveRegistry.objects.get(alarm_id='alarm_id')

        # Asserts:
        self.assertEqual(
            retrieved_reg.status,
            int(ShelveRegistryStatus.get_choices_by_name()['UNSHELVED']),
            'Solved registry status must be closed (0)'
        )
        self.assertEqual(
            retrieved_reg.unshelved_at, resolution_dt,
            'When the registry is unshelved the unshelved_at time must be \
            greater than the shelved_at datetime'
        )
        self.assertEqual(
            response, 'unshelved',
            'Valid resolution is not unshelved correctly'
        )
