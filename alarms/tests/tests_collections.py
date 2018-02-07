from django.test import TestCase
from alarms.models import Alarm
from alarms.tests.factories import AlarmFactory
from alarms.collections import AlarmCollection
from cdb.models import Iasio
from freezegun import freeze_time
import datetime
import time


class TestAlarmsAppInitialization(TestCase):

    def setUp(self):
        """TestCase setup"""
        self.iasio_alarm = Iasio(io_id="AlarmType-ID",
                                 short_desc="Test iasio",
                                 refresh_rate=1000,
                                 ias_type="alarm")
        self.iasio_alarm.save()
        self.iasio_double = Iasio(io_id="DoubleType-ID",
                                  short_desc="Test iasio",
                                  refresh_rate=1000,
                                  ias_type="double")
        self.iasio_double.save()

    def tearDown(self):
        """TestCase teardown"""
        Iasio.objects.all().delete()

    def test_initialize_alarms(self):
        self.assertNotEqual(
            AlarmCollection.singleton_collection, None,
            'The alarm collection was not initialized'
        )

    @freeze_time("2012-01-14")
    def test_initial_alarms_creation(self):
        """Test if the alarm dictionary is populated with cdb data"""
        # Arrange:
        current_time_millis = int(round(time.time() * 1000))
        expected_alarms = [
            Alarm(
                value=1,
                mode='7',
                validity='0',
                core_timestamp=current_time_millis,
                core_id=self.iasio_alarm.io_id,
                running_id='({}:IASIO)'.format(self.iasio_alarm.io_id)
            )
        ]
        # Act:
        AlarmCollection.reset()
        new_count = len(AlarmCollection.get_alarms_list())
        # Assert:
        expected_alarms = [a.to_dict() for a in expected_alarms]
        retrieved_alarms = [
            a.to_dict() for a in AlarmCollection.get_alarms_list()
        ]
        self.assertEqual(
            new_count, 1, 'Unexpected number of alarms after initialization'
        )
        self.assertEqual(
            expected_alarms, retrieved_alarms,
            'Unexpected dictionary of alarms after initialization'
        )

    def test_create_old_alarm(self):
        """ Test if an alarm never created before to the alarm collection is
        created even if it is old """
        # Arrange:
        AlarmCollection.reset()
        old_alarm = Alarm(
            value=1,
            mode='7',
            validity='0',
            core_timestamp=10000,
            core_id='OLD-ALARM',
            running_id='({}:IASIO)'.format('OLD-ALARM')
        )
        # Act:
        status = AlarmCollection.create_or_update_if_latest(old_alarm)
        # Assert:
        self.assertEqual(
            status, 'created-alarm',
            'The status must be created-alarm'
        )
        self.assertTrue(
            'OLD-ALARM' in AlarmCollection.get_alarms(),
            'New alarms should be created'
        )

    def test_ignore_old_alarm(self):
        """ Test if an alarm older than a stored alarm with the same core_id
        is ignored """
        # Arrange:
        AlarmCollection.reset()
        old_alarm = Alarm(
            value=1,
            mode='7',
            validity='0',
            core_timestamp=100,
            core_id=self.iasio_alarm.io_id,
            running_id='({}:IASIO)'.format(self.iasio_alarm.io_id)
        )
        # Act:
        status = AlarmCollection.create_or_update_if_latest(old_alarm)
        # Assert:
        self.assertEqual(
            status, 'ignored-old-alarm',
            'The status must be ignored-old-alarm'
        )
        self.assertNotEqual(
            AlarmCollection.get_alarm(self.iasio_alarm.io_id).core_timestamp,
            100,
            'An older alarm than the stored alarm must not be created'
        )

    def test_update_alarm(self):
        """ Test if an alarm with a timestamp higher than a stored alarm with
        the same core_id is updated correctly """
        # Arrange:
        AlarmCollection.reset()
        current_time_millis = int(round(time.time() * 1000))
        new_alarm = Alarm(
            value=1,
            mode='7',
            validity='0',
            core_timestamp=current_time_millis,
            core_id=self.iasio_alarm.io_id,
            running_id='({}:IASIO)'.format(self.iasio_alarm.io_id)
        )
        # Act:
        status = AlarmCollection.create_or_update_if_latest(new_alarm)
        # Assert:
        self.assertEqual(
            status, 'updated-alarm',
            'The status must be updated-alarm'
        )
        self.assertEqual(
            AlarmCollection.get_alarm(self.iasio_alarm.io_id).core_timestamp,
            current_time_millis,
            'A newer alarm than the stored alarm must be updated'
        )

    def test_recalculation_alarms_validity(self):
        """ Test if the alarms in the AlarmCollection are revalidated """
        # Arrange:
        # Prepare the AlarmCollection with valid alarms and current timestamp
        AlarmCollection.reset()
        alarm_keys = ['AlarmType-ID', 'AlarmType-ID1', 'AlarmType-ID2']
        for core_id in alarm_keys:
            alarm = AlarmFactory.get_valid_alarm(core_id=core_id)
            AlarmCollection.create_or_update_if_latest(alarm)
        initial_alarm_list = [
            a.to_dict() for a in AlarmCollection.get_alarms_list()
        ]
        # Act:
        # Recalculate the AlarmCollection validation after 5 seconds
        initial_time = datetime.datetime.now() + datetime.timedelta(seconds=5)
        with freeze_time(initial_time):
            AlarmCollection.update_all_alarms_validity()
        final_alarm_list = [
            a.to_dict() for a in AlarmCollection.get_alarms_list()
        ]
        # Assert:
        self.assertNotEqual(
            final_alarm_list, initial_alarm_list,
            'The alarms in the AlarmCollection are not invalidated as expected'
        )
        for alarm in AlarmCollection.get_alarms_list():
            self.assertEqual(
                alarm.validity, '0',
                'The alarm {} was not correctly invalidated'.format(
                    alarm.core_id)
            )
