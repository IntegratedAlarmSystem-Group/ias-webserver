import datetime
import time
import pytest
from freezegun import freeze_time
from django.test import TestCase
from alarms.models import Alarm, Validity
from alarms.tests.factories import AlarmFactory
from alarms.collections import AlarmCollection
from cdb.models import Iasio


class TestAlarmsAppInitialization(TestCase):
    """
    This class defines the test suite for the initializaiton of the Alarms app
    """

    def setUp(self):
        """TestCase setup, executed before each test of the TestCase"""
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
        """TestCase teardown, executed after each test of the TestCase"""
        Iasio.objects.all().delete()

    def test_initialize(self):
        """ Test that the alarm collection is initialised on startup """
        self.assertNotEqual(
            AlarmCollection.singleton_collection, None,
            'The alarm collection was not initialized'
        )


class TestAlarmsCollection:
    """This class defines the test suite for the Alarms Collection"""

    @freeze_time("2012-01-14")
    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_create_old_alarm(self):
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
        status = await AlarmCollection.add_or_update_and_notify(old_alarm)
        # Assert:
        assert status == 'created-alarm', 'The status must be created-alarm'
        assert 'OLD-ALARM' in AlarmCollection.get_all_as_dict(), \
            'New alarms should be created'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_update_alarm(self):
        """ Test if an alarm with a timestamp higher than a stored alarm with
        the same core_id is updated correctly """
        # Arrange:
        old_timestamp = int(round(time.time() * 1000))
        new_timestamp = old_timestamp + 10
        AlarmCollection.reset()
        core_id = 'MOCK-ALARM'
        old_alarm = Alarm(
            value=1,
            mode='7',
            validity='0',
            core_timestamp=old_timestamp,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        await AlarmCollection.add_or_update_and_notify(old_alarm)
        new_alarm = Alarm(
            value=1,
            mode='7',
            validity='0',
            core_timestamp=new_timestamp,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        # Act:
        status = await AlarmCollection.add_or_update_and_notify(new_alarm)
        # Assert:
        assert status == 'updated-alarm', 'The status must be updated-alarm'
        timestamp = \
            AlarmCollection.get('MOCK-ALARM').core_timestamp
        assert timestamp == new_timestamp, \
            'A newer alarm than the stored alarm must be updated'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_ignore_old_alarm(self):
        """ Test if an alarm older than a stored alarm with the same core_id
        is ignored """
        # Arrange:
        old_timestamp = int(round(time.time() * 1000))
        new_timestamp = old_timestamp - 10
        AlarmCollection.reset()
        core_id = 'MOCK-ALARM'
        old_alarm = Alarm(
            value=1,
            mode='7',
            validity='0',
            core_timestamp=old_timestamp,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        await AlarmCollection.add_or_update_and_notify(old_alarm)
        new_alarm = Alarm(
            value=1,
            mode='7',
            validity='0',
            core_timestamp=new_timestamp,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        # Act:
        status = await AlarmCollection.add_or_update_and_notify(new_alarm)
        # Assert:
        assert status == 'ignored-old-alarm', \
            'The status must be ignored-old-alarm'

        timestamp = \
            AlarmCollection.get('MOCK-ALARM').core_timestamp

        assert timestamp == old_timestamp, \
            'An older alarm than the stored must not be updated'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_recalculation_alarms_validity(self):
        """ Test if the alarms in the AlarmCollection are revalidated """
        # Arrange:
        # Prepare the AlarmCollection with valid alarms and current timestamp
        AlarmCollection.reset()
        alarm_keys = ['AlarmType-ID', 'AlarmType-ID1', 'AlarmType-ID2']
        for core_id in alarm_keys:
            alarm = AlarmFactory.get_valid_alarm(core_id=core_id)
            await AlarmCollection.add_or_update_and_notify(alarm)
        initial_alarm_list = [
            a.to_dict() for a in AlarmCollection.get_all_as_list()
        ]
        # Act:
        # Recalculate the AlarmCollection validation after 5 seconds
        max_interval = Validity.refresh_rate() + Validity.delta() + 1
        max_timedelta = datetime.timedelta(milliseconds=max_interval)
        initial_time = datetime.datetime.now() + max_timedelta
        with freeze_time(initial_time):
            AlarmCollection.update_all_alarms_validity()
        final_alarm_list = [
            a.to_dict() for a in AlarmCollection.get_all_as_list()
        ]
        # Assert:
        assert final_alarm_list != initial_alarm_list, \
            'The alarms in the AlarmCollection are not invalidated as expected'

        for alarm in AlarmCollection.get_all_as_list():
            assert alarm.validity == '0', \
                'The alarm {} was not correctly invalidated'.format(
                    alarm.core_id)
