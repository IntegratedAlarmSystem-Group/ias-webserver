import datetime
import time
import pytest
from freezegun import freeze_time
from alarms.models import Alarm, IASValue
from alarms.tests.factories import AlarmFactory
from alarms.collections import AlarmCollection
from alarms.connectors import CdbConnector, TicketConnector, PanelsConnector


class TestAlarmsCollectionHandling:
    """ This class defines the test suite for the Alarms Collection
    general handling """

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
            mode=7,
            validity=0,
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
    async def test_update_alarm_and_ntify(self, mocker):
        """ Test if an alarm with a different relevant field
        (in this case validity) and a timestamp higher than before
        is updated correctly and notified to observers """
        # Arrange:
        mocker.spy(AlarmCollection, 'notify_observers')
        old_timestamp = int(round(time.time() * 1000))
        new_timestamp = old_timestamp + 10
        description = 'my-description'
        url = 'dummy-url'
        AlarmCollection.reset()
        core_id = 'MOCK-ALARM'
        old_alarm = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=old_timestamp,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id),
            description=description,
            url=url
        )
        await AlarmCollection.add_or_update_and_notify(old_alarm)
        new_alarm = Alarm(
            value=1,
            mode=7,
            validity=1,
            core_timestamp=new_timestamp,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        # Act:
        status = await AlarmCollection.add_or_update_and_notify(new_alarm)
        # Assert:
        assert status == 'updated-alarm', 'The status must be updated-alarm'
        alarm = AlarmCollection.get('MOCK-ALARM')
        assert alarm.core_timestamp == new_timestamp, \
            'A newer alarm than the stored alarm must be updated'
        assert alarm.description == description, \
            'The alarm description was not maintained'
        assert alarm.url == url, \
            'The alarm url was not maintained'
        assert AlarmCollection.notify_observers.call_count == 2, \
            'Observers should have been notified twice: create and update'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_update_alarm_no_notification(self, mocker):
        """ Test if an alarm with no different relevant fields and a timestamp
        higher than before is updated correctly but not notified """
        # Arrange:
        mocker.spy(AlarmCollection, 'notify_observers')
        old_timestamp = int(round(time.time() * 1000))
        new_timestamp = old_timestamp + 10
        description = 'my-description'
        url = 'dummy-url'
        AlarmCollection.reset()
        core_id = 'MOCK-ALARM'
        old_alarm = Alarm(
            value=1,
            mode=7,
            validity=1,
            core_timestamp=old_timestamp,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id),
            description=description,
            url=url
        )
        await AlarmCollection.add_or_update_and_notify(old_alarm)
        new_alarm = Alarm(
            value=1,
            mode=7,
            validity=1,
            core_timestamp=new_timestamp,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        # Act:
        status = await AlarmCollection.add_or_update_and_notify(new_alarm)
        # Assert:
        assert status == 'updated-alarm', 'The status must be updated-alarm'
        alarm = AlarmCollection.get('MOCK-ALARM')
        assert alarm.core_timestamp == new_timestamp, \
            'A newer alarm than the stored alarm must be updated'
        assert alarm.description == description, \
            'The alarm description was not maintained'
        assert alarm.url == url, \
            'The alarm url was not maintained'
        assert AlarmCollection.notify_observers.call_count == 1, \
            'Observers should have been notified only once: create, not update'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_record_parent_reference(self):
        """ Test if an alarm with dependencies is created, it records itself as
        a parent of its dependencies """
        # Arrange:
        AlarmCollection.reset()
        child = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=10000,
            core_id='child_id',
            running_id='({}:IASIO)'.format('child_id'),
            dependencies=[]
        )
        await AlarmCollection.add_or_update_and_notify(child)
        alarm = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=10000,
            core_id='core_id',
            running_id='({}:IASIO)'.format('core_id'),
            dependencies=['child_id']
        )
        # Act:
        status = await AlarmCollection.add_or_update_and_notify(alarm)
        # Assert:
        assert status == 'created-alarm', 'The status must be created-alarm'
        assert 'core_id' in AlarmCollection.get_all_as_dict(), \
            'New alarms should be created'
        assert 'core_id' in AlarmCollection._get_parents('child_id'), \
            'The alarm core_id should be added as a parent of the dependency \
            alarm in the collection'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_record_multiple_parent_references(self):
        """ Test if an alarm with dependencies is created, and the alarms in the
        dependencies already have another parent, it adds itself to the list of
        parents associated with the alarm in the dependencies
        """
        # Arrange:
        AlarmCollection.reset()
        child = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=10000,
            core_id='child_id',
            running_id='({}:IASIO)'.format('child_id'),
            dependencies=[]
        )
        await AlarmCollection.add_or_update_and_notify(child)
        alarm_1 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=10000,
            core_id='core_id_1',
            running_id='({}:IASIO)'.format('core_id_1'),
            dependencies=['child_id']
        )
        alarm_2 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=10000,
            core_id='core_id_2',
            running_id='({}:IASIO)'.format('core_id_2'),
            dependencies=['child_id']
        )
        # Act:
        status_1 = await AlarmCollection.add_or_update_and_notify(alarm_1)
        status_2 = await AlarmCollection.add_or_update_and_notify(alarm_2)
        # Assert:
        assert status_1 == 'created-alarm' and status_2 == 'created-alarm', \
            'The status of both must be created-alarm'
        assert 'core_id_1' in AlarmCollection.get_all_as_dict() and \
            'core_id_2' in AlarmCollection.get_all_as_dict(), \
            'New alarms should be created'
        parents = AlarmCollection._get_parents('child_id')
        assert 'core_id_1' in parents and 'core_id_2' in parents, \
            'The core_id of the both parent alarms should be added as a parent \
            of dependency alarm in the collection'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_get_dependencies_recursively(self):
        """ Test if the AlarmCollection can retrieve the list of dependencies
        of an alarm including itself"""
        # Arrange:
        timestamp_1 = int(round(time.time() * 1000))
        AlarmCollection.reset()
        # Create two alarms without dependencies alarm_1 and alarm_2
        core_id_1 = 'MOCK-SET-ALARM-1'
        alarm_1 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_1,
            running_id='({}:IASIO)'.format(core_id_1),
            ack=False
        )
        core_id_2 = 'MOCK-SET-ALARM-2'
        alarm_2 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_2,
            running_id='({}:IASIO)'.format(core_id_2),
            ack=False
        )
        # Create an Alarm with alarm_1 as dependency
        core_id_3 = 'MOCK-SET-ALARM-3'
        alarm_3 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_3,
            running_id='({}:IASIO)'.format(core_id_3),
            dependencies=[core_id_1],
            ack=False
        )
        # Create an Alarm with alarm_2 and alarm_3 as dependency
        core_id_4 = 'MOCK-SET-ALARM-4'
        alarm_4 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_4,
            running_id='({}:IASIO)'.format(core_id_4),
            dependencies=[core_id_2, core_id_3],
            ack=False
        )
        # Create an Alarm with alarm_4 as dependecy
        core_id_5 = 'MOCK-SET-ALARM-5'
        alarm_5 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_5,
            running_id='({}:IASIO)'.format(core_id_5),
            dependencies=[core_id_4],
            ack=False
        )
        await AlarmCollection.add_or_update_and_notify(alarm_1)
        await AlarmCollection.add_or_update_and_notify(alarm_2)
        await AlarmCollection.add_or_update_and_notify(alarm_3)
        await AlarmCollection.add_or_update_and_notify(alarm_4)
        await AlarmCollection.add_or_update_and_notify(alarm_5)
        # Act:
        dependencies = AlarmCollection.get_dependencies_recursively(core_id_5)
        # Assert:
        expected_dependencies = [
            core_id_1, core_id_2, core_id_3, core_id_4, core_id_5
        ]
        assert sorted(dependencies) == expected_dependencies, \
            'The method is not returning the list of dependencies correctly'

        # Act:
        dependencies = AlarmCollection.get_dependencies_recursively(core_id_1)
        # Assert:
        expected_dependencies = [core_id_1]
        assert dependencies == expected_dependencies, \
            'The method is not returning the list of dependencies correctly'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_get_ancestors_recursively(self):
        """ Test if the AlarmCollection can retrieve the list of ancestors """
        # Arrange:
        AlarmCollection.reset()
        child = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=10000,
            core_id='child_id',
            running_id='({}:IASIO)'.format('child_id'),
            dependencies=[]
        )
        await AlarmCollection.add_or_update_and_notify(child)
        alarm_1 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=10000,
            core_id='core_id_1',
            running_id='({}:IASIO)'.format('core_id_1'),
            dependencies=['child_id']
        )
        alarm_2 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=10000,
            core_id='core_id_2',
            running_id='({}:IASIO)'.format('core_id_2'),
            dependencies=['child_id']
        )
        await AlarmCollection.add_or_update_and_notify(alarm_1)
        await AlarmCollection.add_or_update_and_notify(alarm_2)
        alarm_3 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=10000,
            core_id='core_id_3',
            running_id='({}:IASIO)'.format('core_id_3'),
            dependencies=['core_id_1']
        )
        await AlarmCollection.add_or_update_and_notify(alarm_3)

        # Act:
        ancestors = AlarmCollection.get_ancestors_recursively('child_id')
        # Assert:
        expected_list_of_ancestors = ['core_id_1', 'core_id_2', 'core_id_3']
        assert sorted(ancestors) == expected_list_of_ancestors, \
            'The method is not returning the list of ancestors correctly'

        # Act:
        ancestors = AlarmCollection.get_ancestors_recursively('core_id_3')
        # Assert:
        expected_list_of_ancestors = []
        assert ancestors == expected_list_of_ancestors, \
            'The method is not returning the list of ancestors correctly'

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
            mode=7,
            validity=0,
            core_timestamp=old_timestamp,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        await AlarmCollection.add_or_update_and_notify(old_alarm)
        new_alarm = Alarm(
            value=1,
            mode=7,
            validity=0,
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
        # Recalculate the AlarmCollection validation after 11 seconds
        max_interval = CdbConnector.validity_threshold + 1
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
            assert alarm.validity == 0, \
                'The alarm {} was not correctly invalidated'.format(
                    alarm.core_id)

    def test_add_value_to_collection(self):
        """ Test if the other types of values are added successfully
        to values_collection """
        # Arrange:
        current_time = int(round(time.time() * 1000))
        ias_value = IASValue(
            value="SOME TEST VALUE",
            mode=5,
            validity=1,
            core_timestamp=current_time,
            core_id="TEST-CORE-ID",
            running_id="FULL-TEST-CORE-ID",
            timestamps={
                'pluginProductionTStamp': current_time,
                'sentToConverterTStamp': current_time,
                'receivedFromPluginTStamp': current_time,
                'convertedProductionTStamp': current_time,
                'sentToBsdbTStamp': current_time,
                'readFromBsdbTStamp': current_time
            }
        )
        value = AlarmCollection.get_value('TEST-CORE-ID')
        assert value is None, \
            'The value must not be in the collection at the beginning'

        # Act:
        AlarmCollection.add_value(ias_value)
        value = AlarmCollection.get_value('TEST-CORE-ID')
        assert value == ias_value, \
            'The value must be in the collection'


class TestAlarmsCollectionAcknowledge:
    """ This class defines the test suite for the Alarms Collection
    acknowledge and ticket handling """

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
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        status = await AlarmCollection.add_or_update_and_notify(alarm_1)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 'created-alarm', 'The status must be created-alarm'
        assert retrieved_alarm.ack is True, \
            'A new CLEARED Alarm must be acknowledged'
        assert AlarmCollection._create_ticket.call_count == 0, \
            'A new Alarm in CLEARED state should not create a new ticket'

        # 2. Change Alarm to SET:
        timestamp_2 = retrieved_alarm.core_timestamp + 100
        alarm_2 = Alarm(
            value=1,
            mode=7,
            validity=0,
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
        await AlarmCollection.acknowledge(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.ack is True, \
            'When the Alarm is acknowledged, its ack status should be True'
        assert AlarmCollection._create_ticket.call_count == 1, \
            'When an Alarm is acknowledged, it should not create a new ticket'

        # 4. Alarm still SET:
        timestamp_4 = retrieved_alarm.core_timestamp + 100
        alarm_4 = Alarm(
            value=1,
            mode=7,
            validity=0,
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
            mode=7,
            validity=0,
            core_timestamp=timestamp_5,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        status = await AlarmCollection.add_or_update_and_notify(alarm_5)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 'updated-alarm', 'The status must be updated-alarm'
        assert retrieved_alarm.ack is True, \
            'When an Alarm changes to CLEAR, its status should still be ack'
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
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_1,
            running_id='({}:IASIO)'.format(core_id_1)
        )
        core_id_2 = 'MOCK-CLEAR-ALARM-2'
        alarm_2 = Alarm(
            value=0,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_2,
            running_id='({}:IASIO)'.format(core_id_2)
        )
        core_id_3 = 'MOCK-SET-ALARM-3'
        alarm_3 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_3,
            running_id='({}:IASIO)'.format(core_id_3)
        )
        core_ids = [
            core_id_1,
            core_id_2,
            core_id_3,
        ]
        await AlarmCollection.add_or_update_and_notify(alarm_1)
        await AlarmCollection.add_or_update_and_notify(alarm_2)
        await AlarmCollection.add_or_update_and_notify(alarm_3)
        # Act:
        ack_alarms_ids = await AlarmCollection.acknowledge(core_ids)
        # Assert:
        retrieved_alarm_1 = AlarmCollection.get(core_id_1)
        retrieved_alarm_2 = AlarmCollection.get(core_id_2)
        retrieved_alarm_3 = AlarmCollection.get(core_id_3)
        assert retrieved_alarm_1.ack is True, \
            'Alarm 1 should have been acknowledged'
        assert retrieved_alarm_2.ack is True, \
            'Alarm 2 should have been acknowledged as it was CLEAR'
        assert retrieved_alarm_3.ack is True, \
            'Alarm 3 should have been acknowledged'
        assert sorted(ack_alarms_ids) == sorted(core_ids), \
            'Acknowledge method did not return the list of expected ack alarms'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_recursive_ack(self, mocker):
        """ Test if the AlarmCollection can acknowledge multiple Alarms
        recursively.
        """
        # Arrange:
        # Mock AlarmCollection._create_ticket to avoid calling it
        mocker.patch.object(AlarmCollection, '_create_ticket')
        timestamp_1 = int(round(time.time() * 1000))
        AlarmCollection.reset()
        # Create two alarms without dependencies alarm_1 and alarm_2
        core_id_1 = 'MOCK-SET-ALARM-1'
        alarm_1 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_1,
            running_id='({}:IASIO)'.format(core_id_1),
            ack=False
        )
        core_id_2 = 'MOCK-SET-ALARM-2'
        alarm_2 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_2,
            running_id='({}:IASIO)'.format(core_id_2),
            ack=False
        )
        # Create an Alarm with alarm_1 as dependency
        core_id_3 = 'MOCK-SET-ALARM-3'
        alarm_3 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_3,
            running_id='({}:IASIO)'.format(core_id_3),
            dependencies=[core_id_1],
            ack=False
        )
        # Create an Alarm with alarm_2 and alarm_3 as dependency
        core_id_4 = 'MOCK-SET-ALARM-4'
        alarm_4 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_4,
            running_id='({}:IASIO)'.format(core_id_4),
            dependencies=[core_id_2, core_id_3],
            ack=False
        )
        # Create an Alarm with alarm_4 as dependecy
        core_id_5 = 'MOCK-SET-ALARM-5'
        alarm_5 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_5,
            running_id='({}:IASIO)'.format(core_id_5),
            dependencies=[core_id_4],
            ack=False
        )
        await AlarmCollection.add_or_update_and_notify(alarm_1)
        await AlarmCollection.add_or_update_and_notify(alarm_2)
        await AlarmCollection.add_or_update_and_notify(alarm_3)
        await AlarmCollection.add_or_update_and_notify(alarm_4)
        await AlarmCollection.add_or_update_and_notify(alarm_5)
        # Act 1: Acknowledge the first leaf
        ack_alarms_ids = await AlarmCollection.acknowledge([core_id_1])
        # Assert
        retrieved_alarm_1 = AlarmCollection.get(core_id_1)
        retrieved_alarm_3 = AlarmCollection.get(core_id_3)
        retrieved_alarm_4 = AlarmCollection.get(core_id_4)
        assert retrieved_alarm_1.ack and retrieved_alarm_3.ack, \
            'The alarm_1 and its parent alarm_3 must be acknowledged'
        assert not retrieved_alarm_4.ack, \
            'The alarm_4 must not be acknowledged because its other \
             child (alarm_2) has not been acknowledge yet'
        assert sorted(ack_alarms_ids) == [core_id_1, core_id_3], \
            'Acknowledge method did not return the list of expected ack alarms'
        # Act 2: Acknowledge the second leaf
        ack_alarms_ids = await AlarmCollection.acknowledge([core_id_2])
        # Assert
        retrieved_alarm_2 = AlarmCollection.get(core_id_2)
        retrieved_alarm_4 = AlarmCollection.get(core_id_4)
        retrieved_alarm_5 = AlarmCollection.get(core_id_5)
        assert retrieved_alarm_2.ack and retrieved_alarm_4.ack and \
            retrieved_alarm_5.ack, \
            'The alarm_2, its parent alarm_4 and its grandparent alarm_5 \
            must be acknowledged'
        assert sorted(ack_alarms_ids) == [core_id_2, core_id_4, core_id_5], \
            'Acknowledge method did not return the list of expected ack alarms'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_recursive_unack(self, mocker):
        """ Test if the AlarmCollection can unacknowledge an alarms and its
        dependent alarms recursively.
        """
        # Arrange:
        # # Mock AlarmCollection._create_ticket to avoid calling it
        mocker.patch.object(AlarmCollection, '_create_ticket')
        timestamp_1 = int(round(time.time() * 1000))
        timestamp_2 = int(round(time.time() * 1000)) + 5
        AlarmCollection.reset()
        # Create two alarms without dependencies alarm_1 and alarm_2, alarm_1
        # is set and alarm_2 is cleared.
        core_id_1 = 'MOCK-SET-ALARM-1'
        alarm_1 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_1,
            running_id='({}:IASIO)'.format(core_id_1),
            ack=False
        )
        core_id_2 = 'MOCK-SET-ALARM-2'
        alarm_2 = Alarm(
            value=0,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_2,
            running_id='({}:IASIO)'.format(core_id_2),
            ack=True
        )
        # Create an Alarm with alarm_1 as dependency
        core_id_3 = 'MOCK-SET-ALARM-3'
        alarm_3 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_3,
            running_id='({}:IASIO)'.format(core_id_3),
            dependencies=[core_id_1],
            ack=False
        )
        # Create an Alarm with alarm_2 and alarm_3 as dependency
        core_id_4 = 'MOCK-SET-ALARM-4'
        alarm_4 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_4,
            running_id='({}:IASIO)'.format(core_id_4),
            dependencies=[core_id_2, core_id_3],
            ack=False
        )
        # Create an Alarm with alarm_4 as dependecy
        core_id_5 = 'MOCK-SET-ALARM-5'
        alarm_5 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id_5,
            running_id='({}:IASIO)'.format(core_id_5),
            dependencies=[core_id_4],
            ack=False
        )
        await AlarmCollection.add_or_update_and_notify(alarm_1)
        await AlarmCollection.add_or_update_and_notify(alarm_2)
        await AlarmCollection.add_or_update_and_notify(alarm_3)
        await AlarmCollection.add_or_update_and_notify(alarm_4)
        await AlarmCollection.add_or_update_and_notify(alarm_5)
        # Act 1: Acknowledge the first leaf alarm_1
        ack_alarms_ids = await AlarmCollection.acknowledge([core_id_1])
        # Assert
        retrieved_alarm_1 = AlarmCollection.get(core_id_1)
        retrieved_alarm_2 = AlarmCollection.get(core_id_2)
        retrieved_alarm_3 = AlarmCollection.get(core_id_3)
        retrieved_alarm_4 = AlarmCollection.get(core_id_4)
        retrieved_alarm_5 = AlarmCollection.get(core_id_5)
        assert retrieved_alarm_2.value == 0 and retrieved_alarm_2.ack, \
            'The alarm_2 remains cleared and acknowledged'
        assert retrieved_alarm_1.ack and retrieved_alarm_3.ack, \
            'The alarm_1 and its parent alarm_3 must be acknowledged'
        assert retrieved_alarm_4.ack and retrieved_alarm_5.ack, \
            'The alarm_4 and its parent alarm_5 must be acknowledged'
        expected_ack_alarms = [core_id_1, core_id_3, core_id_4, core_id_5]
        assert sorted(ack_alarms_ids) == expected_ack_alarms, \
            'Acknowledge method did not return the list of expected ack alarms'
        # Act 2: Change from cleared to set the second leaf alarm_2
        new_alarm_2 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_2,
            core_id=core_id_2,
            running_id='({}:IASIO)'.format(core_id_2)
        )
        await AlarmCollection.add_or_update_and_notify(new_alarm_2)
        # Assert
        retrieved_alarm_1 = AlarmCollection.get(core_id_1)
        retrieved_alarm_2 = AlarmCollection.get(core_id_2)
        retrieved_alarm_3 = AlarmCollection.get(core_id_3)
        retrieved_alarm_4 = AlarmCollection.get(core_id_4)
        retrieved_alarm_5 = AlarmCollection.get(core_id_5)
        assert not retrieved_alarm_2.ack, \
            'The alarm_2 must be unacknowleged'
        assert retrieved_alarm_1.ack and retrieved_alarm_3.ack, \
            'The alarm_1 and its parent alarm_3 must remain acknowledged'
        assert not retrieved_alarm_4.ack, \
            'The parent of alarm_2 (alarm_4) must be unacknowleged'
        assert not retrieved_alarm_5.ack, \
            'The grandparent of alarm_2 (alarm_5) must be unacknowleged'

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
    async def test_new_set_alarm_ticket_is_updated_when_cleared(self, mocker):
        """ Test if a ticket is created when a new SET Alarm arrives,
        and if the ticket is updated to cleared_ack or cleared_unack states
        accordingly when the Alarm changes to Clear """

        # Mock AlarmCollection._create_ticket to assert if it was called
        # and avoid calling the real function
        mocker.patch.object(AlarmCollection, '_create_ticket')
        mocker.patch.object(AlarmCollection, '_clear_ticket')

        # 1. Create SET Alarm:
        timestamp_1 = int(round(time.time() * 1000))
        AlarmCollection.reset()
        core_id = 'MOCK-ALARM'
        alarm_1 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        status = await AlarmCollection.add_or_update_and_notify(alarm_1)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 'created-alarm', 'The status must be created-alarm'
        assert retrieved_alarm.ack is False, \
            'A new Alarm must not be acknowledged'
        assert AlarmCollection._create_ticket.call_count == 1, \
            'A new Alarm in SET state should create a new ticket'

        # 2. Change Alarm to CLEAR:
        alarm_1 = Alarm(
            value=0,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1+100,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id)
        )
        status = await AlarmCollection.add_or_update_and_notify(alarm_1)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 'updated-alarm', 'The status must be updated-alarm'
        assert retrieved_alarm.ack is False, \
            'the Alarm must not be acknowledged when it changes to CLEAR'
        assert AlarmCollection._clear_ticket.call_count == 1, \
            'When the Alarm changes CLEAR, the ticket should be updated'


class TestAlarmsCollectionShelve:
    """ This class defines the test suite for the Alarms Collection
    shelve and registry handling """

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_alarm_shelving(self):
        """ Test if an alarm can be shelved and unshelved """
        # 1. Create Alarm:
        timestamp_1 = int(round(time.time() * 1000))
        AlarmCollection.reset()
        core_id = 'MOCK-ALARM'
        alarm_1 = Alarm(
            value=0,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id),
            can_shelve=True
        )
        status = await AlarmCollection.add_or_update_and_notify(alarm_1)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 'created-alarm', 'The status must be created-alarm'
        assert retrieved_alarm.shelved is False, \
            'A new Alarm must be unshelved'

        # 2. Shelve Alarm:
        status = await AlarmCollection.shelve(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 1, 'The status must be 1'
        assert retrieved_alarm.shelved is True, \
            'When an Alarm is shelved its shelved status should be True'

        # 3. Unshelve Alarm:
        status = await AlarmCollection.unshelve(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status is True, 'The status must be True'
        assert retrieved_alarm.shelved is False, \
            'When an Alarm is unshelved its shelved status should be False'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_forbid_alarm_shelving(self):
        """ Test if a non-shelvable alarm cannot be shelved and unshelved """
        # 1. Create Alarm:
        timestamp_1 = int(round(time.time() * 1000))
        AlarmCollection.reset()
        core_id = 'MOCK-ALARM'
        alarm_1 = Alarm(
            value=0,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id),
            can_shelve=False
        )
        status = await AlarmCollection.add_or_update_and_notify(alarm_1)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 'created-alarm', 'The status must be created-alarm'
        assert retrieved_alarm.shelved is False, \
            'A new Alarm must be unshelved'

        # 2. Shelve Alarm:
        status = await AlarmCollection.shelve(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status is -1, 'The status must be -1'
        assert retrieved_alarm.shelved is False, \
            'When an Alarm is not shelved its shelved status should be False'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_already_shelved_alarm(self):
        """ Test if an already shelved alarm cannot be shelved """
        # 1. Create Alarm:
        timestamp_1 = int(round(time.time() * 1000))
        AlarmCollection.reset()
        core_id = 'MOCK-ALARM'
        alarm_1 = Alarm(
            value=0,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id),
            can_shelve=True
        )
        status = await AlarmCollection.add_or_update_and_notify(alarm_1)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 'created-alarm', 'The status must be created-alarm'
        assert retrieved_alarm.shelved is False, \
            'A new Alarm must be unshelved'

        # 2. Shelve Alarm:
        status = await AlarmCollection.shelve(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 1, 'The status must be 1'
        assert retrieved_alarm.shelved is True, \
            'When an Alarm is shelved its shelved status should be True'

        # 3. Shelve Alarm again:
        status = await AlarmCollection.shelve(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 0, 'The status must be 0'
        assert retrieved_alarm.shelved is True, \
            'When an Alarm is shelved its shelved status should be True'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_no_ticket_for_shelved_alarm(self, mocker):
        """ Test if tickets are not created for Alarms in shelved status """
        # Mock AlarmCollection._create_ticket to assert if it was called
        # and avoid calling the real function
        mocker.patch.object(AlarmCollection, '_create_ticket')

        # 1. Create Alarm:
        timestamp_1 = int(round(time.time() * 1000))
        AlarmCollection.reset()
        core_id = 'MOCK-ALARM'
        alarm_1 = Alarm(
            value=0,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id),
            can_shelve=True
        )
        status = await AlarmCollection.add_or_update_and_notify(alarm_1)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 'created-alarm', 'The status must be created-alarm'
        assert retrieved_alarm.ack is True, \
            'A new CLEARED Alarm must be acknowledged'
        assert AlarmCollection._create_ticket.call_count == 0, \
            'A new Alarm in CLEARED state should not create a new ticket'

        # 2. Shelve Alarm:
        status = await AlarmCollection.shelve(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status is 1, 'The status must be 1'
        assert retrieved_alarm.shelved is True, \
            'When an Alarm is shelved its shelved status should be True'

        # 3. Change Alarm to SET:
        alarm_2 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=timestamp_1 + 100,
            core_id=core_id,
            running_id='({}:IASIO)'.format(core_id),
        )
        status = await AlarmCollection.add_or_update_and_notify(alarm_2)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 'updated-alarm', 'The status must be updated-alarm'
        assert retrieved_alarm.ack is True, \
            'When a shelved Alarm changes to SET, its ack should not change'
        assert AlarmCollection._create_ticket.call_count == 0, \
            'When a shelved Alarm changes to SET, a new ticket should not be \
            created'


class TestIasValueUpdates:
    """ This class defines the test suite for the Alarms Collection management
    of IASValues that are not of type Alarm """

    @pytest.mark.django_db
    def test_add_value(self):
        """ Test if the value is added to the values collection """
        # Arrange:
        AlarmCollection.reset()
        timestamp = int(round(time.time() * 1000))
        value = IASValue(
            value="SOME_VALUE",
            mode=5,
            validity=1,
            core_timestamp=timestamp,
            core_id='dummy_value',
            running_id='dummy_value',
        )
        assert 'dummy_value' not in AlarmCollection.values_collection

        # Act:
        AlarmCollection.add_value(value)
        new_value = AlarmCollection.values_collection['dummy_value']

        # Assert:
        assert new_value == value, \
            'The value was not the expected'

    @pytest.mark.django_db
    def test_get_value(self):
        """ Test if the AlarmCollection can get a value from the collection"""
        # Arrange:
        AlarmCollection.reset()
        timestamp = int(round(time.time() * 1000))
        value = IASValue(
            value="SOME_VALUE",
            mode=5,
            validity=1,
            core_timestamp=timestamp,
            core_id='dummy_value',
            running_id='dummy_value',
        )
        assert 'dummy_value' not in AlarmCollection.values_collection
        AlarmCollection.add_value(value)

        # Act:
        new_value = AlarmCollection.get_value('dummy_value')

        # Assert:
        assert new_value == value, \
            'The value was not the expected'

    @pytest.mark.django_db
    def test_add_or_update_value(self, mocker):
        """ Test if the AlarmCollection can add or update a value """
        # Mock PanelsConnector.update_antennas_configuration to assert if it
        # was called and avoid calling the real function
        mocker.patch.object(PanelsConnector, 'update_antennas_configuration')

        # Arrange:
        AlarmCollection.reset()
        timestamp = int(round(time.time() * 1000))
        value_1 = IASValue(
            value="SOME_VALUE",
            mode=5,
            validity=1,
            core_timestamp=timestamp,
            core_id='dummy_value',
            running_id='dummy_value',
        )
        value_2 = IASValue(
            value="SOME_VALUE_UPDATED",
            mode=5,
            validity=1,
            core_timestamp=timestamp+1,
            core_id='dummy_value',
            running_id='dummy_value',
        )
        assert 'dummy_value' not in AlarmCollection.values_collection

        # Act:
        status = AlarmCollection.add_or_update_value(value_1)
        new_value = AlarmCollection.get_value('dummy_value')

        # Assert:
        assert status == 'created-value'
        assert new_value == value_1, \
            'The value was not the expected'
        assert PanelsConnector.update_antennas_configuration.call_count == 0, \
            'When the value received is not an AntennasToPads update the \
            panels connector should not update the database'

        # Act:
        status = AlarmCollection.add_or_update_value(value_2)
        new_value = AlarmCollection.get_value('dummy_value')

        # Assert:
        assert status == 'updated-different'
        assert new_value.value == value_2.value, \
            'The value was not the expected'
        assert new_value.state_change_timestamp != 0, \
            'The state change timestamp was not updated'
        assert PanelsConnector.update_antennas_configuration.call_count == 0, \
            'When the value received is not an AntennasToPads update the \
            panels connector should not update the database'

    @pytest.mark.django_db
    def test_add_or_update_antennas_pad_value(self, mocker):
        """
        Test if the AlarmCollection can add or update an antennas-pad value
        """
        # Mock PanelsConnector.update_antennas_configuration to assert if it
        # was called and avoid calling the real function
        mocker.patch.object(PanelsConnector, 'update_antennas_configuration')

        # Arrange:
        AlarmCollection.reset()
        timestamp = int(round(time.time() * 1000))
        value = IASValue(
            value="A000:PAD0,A001:PAD1,A002:PAD2",
            mode=5,
            validity=1,
            core_timestamp=timestamp,
            core_id='Array-AntennasToPads',
            running_id='Array-AntennasToPads',
        )

        # Act:
        AlarmCollection.add_or_update_value(value)

        # Assert:
        assert PanelsConnector.update_antennas_configuration.call_count == 1, \
            'When the value received is an AntennasToPads update the panels \
            connector should update the database'

    @pytest.mark.django_db
    def test_initialize(self, mocker):
        """ Test the AlarmCollection initialization """
        # Arrange:
        mock_ids = [
            'mock_alarm_1',
            'mock_alarm_3',
            'mock_alarm_4',
        ]
        mock_iasios = [
            {
                "id": "mock_alarm_0",
                "shortDesc": "Dummy Iasio of type ALARM 0",
                "iasType": "ALARM",
                "docUrl": "http://www.alma0.cl"
            },
            {
                "id": "mock_alarm_1",
                "shortDesc": "Dummy Iasio of type ALARM 1",
                "iasType": "ALARM",
                "docUrl": "http://www.alma1.cl"
            },
            {
                "id": "mock_alarm_2",
                "shortDesc": "Dummy Iasio of type ALARM 2",
                "iasType": "ALARM",
                "docUrl": "http://www.alma2.cl"
            },
            {
                "id": "mock_alarm_3",
                "shortDesc": "Dummy Iasio of type ALARM 3",
                "iasType": "ALARM",
                "docUrl": "http://www.alma3.cl"
            },
        ]
        expected_alarm_ids = sorted([
            'mock_alarm_0',
            'mock_alarm_1',
            'mock_alarm_2',
            'mock_alarm_3',
            'mock_alarm_4',
        ])
        expected_alarm_descriptions = sorted([
            mock_iasios[0]['shortDesc'],
            mock_iasios[1]['shortDesc'],
            mock_iasios[2]['shortDesc'],
            mock_iasios[3]['shortDesc'],
            '',
        ])
        expected_alarm_urls = sorted([
            mock_iasios[0]['docUrl'],
            mock_iasios[1]['docUrl'],
            mock_iasios[2]['docUrl'],
            mock_iasios[3]['docUrl'],
            '',
        ])
        PanelsConnector_get_alarm_ids_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarm_ids_of_alarm_configs'
            )

        CdbConnector_get_iasios = mocker.patch.object(
            CdbConnector, 'get_iasios'
        )
        PanelsConnector_get_alarm_ids_of_alarm_configs.return_value = mock_ids
        CdbConnector_get_iasios.return_value = mock_iasios
        # Act:
        AlarmCollection.reset()
        # Assert:
        alarms = AlarmCollection.get_all_as_list()
        retrieved_alarms_ids = sorted([a.core_id for a in alarms])
        retrieved_alarms_descriptions = sorted([a.description for a in alarms])
        retrieved_alarms_urls = sorted([a.url for a in alarms])
        assert retrieved_alarms_ids == expected_alarm_ids
        assert retrieved_alarms_descriptions == expected_alarm_descriptions
        assert retrieved_alarms_urls == expected_alarm_urls
