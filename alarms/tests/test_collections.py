from django.test import TestCase
from alarms.models import Alarm
from alarms.collections import AlarmCollection
from cdb.models import Iasio
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
        AlarmCollection.delete_alarms()

    def tearDown(self):
        """TestCase teardown"""
        Iasio.objects.all().delete()

    def test_initial_alarms_creation(self):
        """Test if the alarm dictionary is populated with cdb data"""
        # Arrange:
        old_count = len(AlarmCollection.get_alarms())
        current_time_millis = int(round(time.time() * 1000))
        expected_alarms = {
            self.iasio_alarm.io_id: Alarm(
                value=1,
                mode='7',
                validity='0',
                core_timestamp=current_time_millis,
                core_id=self.iasio_alarm.io_id,
                running_id='({}:IASIO)'.format(self.iasio_alarm.io_id)
            )
        }
        # Act:
        AlarmCollection.initialize_alarms()
        new_count = len(AlarmCollection.get_alarms())
        # Assert:
        self.assertEqual(
            old_count, 0,
            'The initial dictionary of alarms is not empty'
        )
        self.assertEqual(
            new_count, 1,
            'Unexpected dictionary of alarms after initialization'
        )
