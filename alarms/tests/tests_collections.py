import datetime
import time
import pytest
from pytest_mock import mocker
from freezegun import freeze_time
from alarms.models import Alarm
from alarms.tests.factories import AlarmFactory
from alarms.collections import AlarmCollection
from alarms.connectors import CdbConnector as CdbConn
from alarms.connectors import TicketConnector


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
    async def test_alarm_cycle(self, mocker):
        """ Test if an alarm with a timestamp higher than a stored alarm with
        the same core_id is updated correctly """

        # Mock AlarmCollection._create_ticket to assert if it was called
        # and avoid calling the real function
        mocker.patch.object(AlarmCollection, '_create_ticket')

        # 1. Create Alarm:
        timestamp_1 = int(round(time.time() * 1000))
        AlarmCollection.reset()
        core_id = 'MOCK-ALARM'
        alarm_1 = Alarm(
            value=0,
            mode='7',
            validity='0',
            core_timestamp=timestamp_1,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        status = await AlarmCollection.add_or_update_and_notify(alarm_1)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 'created-alarm', 'The status must be created-alarm'
        assert retrieved_alarm.ack is False, \
            'A new Alarm must not be acknowledged'
        assert AlarmCollection._create_ticket.call_count == 0, \
            'A new Alarm in CLEAR state should not create a new ticket'

        # 2. Change Alarm to SET:
        timestamp_2 = retrieved_alarm.core_timestamp + 100
        alarm_2 = Alarm(
            value=1,
            mode='7',
            validity='0',
            core_timestamp=timestamp_2,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        status = await AlarmCollection.add_or_update_and_notify(alarm_2)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 'updated-alarm', 'The status must be updated-alarm'
        assert retrieved_alarm.ack is False, \
            'When an Alarm changes to SET, it should not be acknowledged'
        assert AlarmCollection._create_ticket.call_count == 1, \
            'When an Alarm changes to SET, a new ticket should be created'

        # 3. Acknowledge Alarm:
        AlarmCollection.acknowledge(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.ack is True, \
            'When the Alarm is acknowledged, its ack status should be True'
        assert AlarmCollection._create_ticket.call_count == 1, \
            'When an Alarm is acknowledged, it should not create a new ticket'

        # 4. Alarm still SET:
        timestamp_4 = retrieved_alarm.core_timestamp + 100
        alarm_4 = Alarm(
            value=1,
            mode='7',
            validity='0',
            core_timestamp=timestamp_4,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        status = await AlarmCollection.add_or_update_and_notify(alarm_4)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 'updated-alarm', 'The status must be updated-alarm'
        assert retrieved_alarm.ack is True, \
            'When an Alarm maintains its value, it should maintain its ack'
        assert AlarmCollection._create_ticket.call_count == 1, \
            'When an Alarm maintains its value, it should not create a ticket'

        # 5. Alarm changes to CLEAR:
        timestamp_5 = retrieved_alarm.core_timestamp + 100
        alarm_5 = Alarm(
            value=0,
            mode='7',
            validity='0',
            core_timestamp=timestamp_5,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        status = await AlarmCollection.add_or_update_and_notify(alarm_5)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 'updated-alarm', 'The status must be updated-alarm'
        assert retrieved_alarm.ack is False, \
            'When an Alarm changes to CLEAR, its ack should be reset'
        assert AlarmCollection._create_ticket.call_count == 1, \
            'When an Alarm changes to CLEAR, it should not create a new ticket'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_ack_multiple_alarms(self, mocker):
        """ Test if the AlarmCollection can acknowledge multiple Alarms """
        # Arrange:
        # Mock AlarmCollection._create_ticket to avoid calling it
        mocker.patch.object(AlarmCollection, '_create_ticket')
        timestamp_1 = int(round(time.time() * 1000))
        AlarmCollection.reset()
        core_id_1 = 'MOCK-SET-ALARM-1'
        alarm_1 = Alarm(
            value=1,
            mode='7',
            validity='0',
            core_timestamp=timestamp_1,
            core_id=core_id_1,
            running_id='({}:IASIO)'.format(core_id_1)
        )
        core_id_2 = 'MOCK-CLEAR-ALARM-2'
        alarm_2 = Alarm(
            value=0,
            mode='7',
            validity='0',
            core_timestamp=timestamp_1,
            core_id=core_id_2,
            running_id='({}:IASIO)'.format(core_id_2)
        )
        core_id_3 = 'MOCK-SET-ALARM-3'
        alarm_3 = Alarm(
            value=1,
            mode='7',
            validity='0',
            core_timestamp=timestamp_1,
            core_id=core_id_3,
            running_id='({}:IASIO)'.format(core_id_3)
        )
        core_ids = [
            core_id_1,
            core_id_2,
            core_id_3,
        ]
        status = await AlarmCollection.add_or_update_and_notify(alarm_1)
        status = await AlarmCollection.add_or_update_and_notify(alarm_2)
        status = await AlarmCollection.add_or_update_and_notify(alarm_3)
        # Act:
        AlarmCollection.acknowledge(core_ids)
        # Assert:
        retrieved_alarm_1 = AlarmCollection.get(core_id_1)
        retrieved_alarm_2 = AlarmCollection.get(core_id_2)
        retrieved_alarm_3 = AlarmCollection.get(core_id_3)
        assert retrieved_alarm_1.ack is True, \
            'Alarm 1 should have been acknowledged'
        assert retrieved_alarm_2.ack is False, \
            'Alarm 2 should not have been acknowledged as it was CLEAR'
        assert retrieved_alarm_3.ack is True, \
            'Alarm 3 should have been acknowledged'

    @pytest.mark.django_db
    def test_create_ticket(self, mocker):
        """
        Test that AlarmCollection._create_ticket calls
        TicketConnector.create_ticket
        """
        # Arrange:
        # Mock TicketConnector.create_ticket to assert if it was called
        # and avoid calling the real function
        mocker.patch.object(TicketConnector, 'create_ticket')
        AlarmCollection.reset()
        core_id = 'MOCK-ALARM'

        # Act:
        AlarmCollection._create_ticket(core_id)

        # Assert:
        assert TicketConnector.create_ticket.call_count == 1, \
            'The ticket was no actually created'

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
        max_interval = CdbConn.refresh_rate + CdbConn.tolerance + 1
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
