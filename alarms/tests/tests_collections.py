import datetime
import time
import pytest
from freezegun import freeze_time
from alarms.models import Alarm, Value, IASValue, OperationalMode, Validity
from alarms.tests.factories import AlarmFactory
from alarms.collections import AlarmCollection
from alarms.connectors import CdbConnector, TicketConnector, PanelsConnector


class TestAlarmsCollectionHandling:
    """ This class defines the test suite for the Alarms Collection general handling """

    @freeze_time("2012-01-14")
    @pytest.mark.django_db
    def test_create_old_alarm(self):
        """ Test if an new alarm is created and notified to observers even if it is old (UNRELIABLE) """
        # Arrange:
        AlarmCollection.reset()
        formatted_current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        iasio = {
            "value": "SET_MEDIUM",
            "productionTStamp": formatted_current_time,
            "sentToBsdbTStamp": formatted_current_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "UNRELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(OLD-ALARM:IASIO)",
            "valueType": "ALARM"
        }
        # Act:
        AlarmCollection.add_or_update_alarm(iasio)
        # Assert:
        assert 'OLD-ALARM' in AlarmCollection.get_all_as_dict(), 'New alarms should be created'
        alarm = AlarmCollection.get('OLD-ALARM')
        assert alarm.validity == Validity.UNRELIABLE.value, 'Alarm validity should be UNRELIABLE'
        assert alarm.value == Value.SET_MEDIUM.value, 'Alarm value does not match Iasio value'
        assert alarm.mode == OperationalMode.OPERATIONAL.value, 'Alarm mode does not match Iasio mode'
        assert 'OLD-ALARM' in AlarmCollection.alarm_changes, 'New alarms should be notified'

    @pytest.mark.django_db
    def test_update_alarm(self):
        """ Test if an alarm with a different relevant field (in this case validity) and a timestamp higher than before
        is updated correctly and notified to observers """
        # Arrange:
        description = 'Mock Alarm Description'
        url = 'www.alma.cl'
        old_time = datetime.datetime.now()
        new_time = old_time + datetime.timedelta(seconds=10)
        iasio_old_time = old_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        iasio_new_time = new_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        alarm_old_time = int((time.mktime(old_time.timetuple()) + old_time.microsecond / 1E6) * 1000)
        alarm_new_time = int((time.mktime(new_time.timetuple()) + new_time.microsecond / 1E6) * 1000)
        AlarmCollection.reset()
        old_iasio = {
            "value": "SET_MEDIUM",
            "productionTStamp": iasio_old_time,
            "sentToBsdbTStamp": iasio_old_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "UNRELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-ALARM:IASIO)",
            "valueType": "ALARM"
        }
        AlarmCollection.add_or_update_alarm(old_iasio)
        alarm = AlarmCollection.get('MOCK-ALARM')
        alarm.description = description
        alarm.url = url
        AlarmCollection.alarm_changes = []
        new_iasio = {
            "value": "SET_HIGH",
            "productionTStamp": iasio_new_time,
            "sentToBsdbTStamp": iasio_new_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "UNRELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-ALARM:IASIO)",
            "valueType": "ALARM"
        }
        # Act:
        AlarmCollection.add_or_update_alarm(new_iasio)
        # Assert:
        alarm = AlarmCollection.get('MOCK-ALARM')
        assert alarm.core_timestamp != alarm_old_time, 'A newer alarm than the stored alarm must be updated'
        assert alarm.core_timestamp == alarm_new_time, 'A newer alarm than the stored alarm must be updated'
        assert alarm.validity == Validity.UNRELIABLE.value, 'Alarm validity should be UNRELIABLE'
        assert alarm.value == Value.SET_HIGH.value, 'Alarm value does not match the new Iasio value'
        assert alarm.mode == OperationalMode.OPERATIONAL.value, 'Alarm mode does not match the Iasio mode'
        assert alarm.description == description, 'The alarm description was not maintained'
        assert alarm.url == url, 'The alarm url was not maintained'
        assert 'MOCK-ALARM' in AlarmCollection.alarm_changes, 'New alarms should be notified'

    @pytest.mark.django_db
    def test_update_alarm_no_notification(self, mocker):
        """ Test if an alarm with no different relevant fields and a timestamp
        higher than before is updated correctly but not notified """
        # Arrange:
        description = 'Mock Alarm Description'
        url = 'www.alma.cl'
        old_time = datetime.datetime.now()
        new_time = old_time + datetime.timedelta(seconds=10)
        iasio_old_time = old_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        iasio_new_time = new_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        alarm_old_time = int((time.mktime(old_time.timetuple()) + old_time.microsecond / 1E6) * 1000)
        alarm_new_time = int((time.mktime(new_time.timetuple()) + new_time.microsecond / 1E6) * 1000)
        AlarmCollection.reset()
        old_iasio = {
            "value": "SET_MEDIUM",
            "productionTStamp": iasio_old_time,
            "sentToBsdbTStamp": iasio_old_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "UNRELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-ALARM:IASIO)",
            "valueType": "ALARM"
        }
        AlarmCollection.add_or_update_alarm(old_iasio)
        alarm = AlarmCollection.get('MOCK-ALARM')
        alarm.description = description
        alarm.url = url
        AlarmCollection.alarm_changes = []
        new_iasio = {
            "value": "SET_MEDIUM",
            "productionTStamp": iasio_new_time,
            "sentToBsdbTStamp": iasio_new_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "UNRELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-ALARM:IASIO)",
            "valueType": "ALARM"
        }
        # Act:
        AlarmCollection.add_or_update_alarm(new_iasio)
        # Assert:
        alarm = AlarmCollection.get('MOCK-ALARM')
        assert alarm.core_timestamp != alarm_old_time, 'A newer alarm than the stored alarm must be updated'
        assert alarm.core_timestamp == alarm_new_time, 'A newer alarm than the stored alarm must be updated'
        assert alarm.validity == Validity.UNRELIABLE.value, 'Alarm validity should be UNRELIABLE'
        assert alarm.value == Value.SET_MEDIUM.value, 'Alarm value does not match the new Iasio value'
        assert alarm.mode == OperationalMode.OPERATIONAL.value, 'Alarm mode does not match the Iasio mode'
        assert alarm.description == description, 'The alarm description was not maintained'
        assert alarm.url == url, 'The alarm url was not maintained'
        assert 'MOCK-ALARM' not in AlarmCollection.alarm_changes, 'New alarms with no change should not be notified'

    @pytest.mark.django_db
    def test_ignore_update_for_older_alarm(self, mocker):
        """ Test if an alarm with an older timestamp is ignored (not updated and not notified) """
        # Arrange:
        description = 'Mock Alarm Description'
        url = 'www.alma.cl'
        old_time = datetime.datetime.now()
        new_time = old_time - datetime.timedelta(milliseconds=1)
        iasio_old_time = old_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        iasio_new_time = new_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        alarm_old_time = int((time.mktime(old_time.timetuple()) + old_time.microsecond / 1E6) * 1000)
        alarm_new_time = int((time.mktime(new_time.timetuple()) + new_time.microsecond / 1E6) * 1000)
        AlarmCollection.reset()
        old_iasio = {
            "value": "SET_MEDIUM",
            "productionTStamp": iasio_old_time,
            "sentToBsdbTStamp": iasio_old_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "UNRELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-ALARM:IASIO)",
            "valueType": "ALARM"
        }
        AlarmCollection.add_or_update_alarm(old_iasio)
        alarm = AlarmCollection.get('MOCK-ALARM')
        alarm.description = description
        alarm.url = url
        AlarmCollection.alarm_changes = []
        new_iasio = {
            "value": "SET_HIGH",
            "productionTStamp": iasio_new_time,
            "sentToBsdbTStamp": iasio_new_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "UNRELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-ALARM:IASIO)",
            "valueType": "ALARM"
        }
        # Act:
        AlarmCollection.add_or_update_alarm(new_iasio)
        # Assert:
        alarm = AlarmCollection.get('MOCK-ALARM')
        assert alarm.core_timestamp == alarm_old_time, 'A newer alarm than the stored alarm must be updated'
        assert alarm.core_timestamp > alarm_new_time, 'A newer alarm than the stored alarm must be updated'
        assert alarm.validity == Validity.UNRELIABLE.value, 'Alarm validity should be UNRELIABLE'
        assert alarm.value == Value.SET_MEDIUM.value, 'Alarm value does not match the new Iasio value'
        assert alarm.mode == OperationalMode.OPERATIONAL.value, 'Alarm mode does not match the Iasio mode'
        assert alarm.description == description, 'The alarm description was not maintained'
        assert alarm.url == url, 'The alarm url was not maintained'
        assert 'MOCK-ALARM' not in AlarmCollection.alarm_changes, 'New alarms with no change should not be notified'

    @pytest.mark.django_db
    def test_recalculation_alarms_validity(self):
        """ Test if the alarms in the AlarmCollection are revalidated """
        # Arrange:
        # Prepare the AlarmCollection with valid alarms and current timestamp
        AlarmCollection.reset([])
        iasio_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        iasios = [
            {
                "value": "SET_MEDIUM",
                "productionTStamp": iasio_time,
                "sentToBsdbTStamp": iasio_time,
                "mode": "OPERATIONAL",   # 5: OPERATIONAL
                "iasValidity": "RELIABLE",
                "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-ALARM1:IASIO)",
                "valueType": "ALARM"
            },
            {
                "value": "SET_MEDIUM",
                "productionTStamp": iasio_time,
                "sentToBsdbTStamp": iasio_time,
                "mode": "OPERATIONAL",   # 5: OPERATIONAL
                "iasValidity": "RELIABLE",
                "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-ALARM2:IASIO)",
                "valueType": "ALARM"
            },
            {
                "value": "SET_MEDIUM",
                "productionTStamp": iasio_time,
                "sentToBsdbTStamp": iasio_time,
                "mode": "OPERATIONAL",   # 5: OPERATIONAL
                "iasValidity": "RELIABLE",
                "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-ALARM3:IASIO)",
                "valueType": "ALARM"
            },
        ]

        for iasio in iasios:
            AlarmCollection.add_or_update_alarm(iasio)
        initial_alarm_list = [a.to_dict() for a in AlarmCollection.get_all_as_list()]
        for alarm in AlarmCollection.get_all_as_list():
            assert alarm.validity == 1, 'The alarm {} should be RELIABLE'.format(alarm.core_id)
        # Act:
        # Recalculate the AlarmCollection validation after 11 seconds
        max_interval = CdbConnector.validity_threshold + 1
        max_timedelta = datetime.timedelta(milliseconds=max_interval)
        initial_time = datetime.datetime.now() + max_timedelta
        with freeze_time(initial_time):
            AlarmCollection.update_all_alarms_validity()
        final_alarm_list = [a.to_dict() for a in AlarmCollection.get_all_as_list()]
        # Assert:
        assert final_alarm_list != initial_alarm_list, \
            'The alarms in the AlarmCollection are not invalidated as expected'
        for alarm in AlarmCollection.get_all_as_list():
            assert alarm.validity == 0, 'The alarm {} was not correctly invalidated'.format(alarm.core_id)

    @pytest.mark.django_db
    def test_record_parent_reference(self):
        """ Test if when an alarm with dependencies is created, it records itself as a parent of its dependencies """
        # Arrange:
        AlarmCollection.reset()
        timestamp = datetime.datetime.now()
        iasio_timestamp = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')
        child_iasio = {
            "value": "SET_MEDIUM",
            "productionTStamp": iasio_timestamp,
            "sentToBsdbTStamp": iasio_timestamp,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(CHILD-ALARM:IASIO)",
            "valueType": "ALARM",
            "depsFullRunningIds": []
        }
        parent_iasio = {
            "value": "SET_MEDIUM",
            "productionTStamp": iasio_timestamp,
            "sentToBsdbTStamp": iasio_timestamp,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(PARENT-ALARM:IASIO)",
            "valueType": "ALARM",
            "depsFullRunningIds": ["(Converter-ID:CONVERTER)@(CHILD-ALARM:IASIO)"]
        }
        AlarmCollection.add_or_update_alarm(child_iasio)
        # Act:
        AlarmCollection.add_or_update_alarm(parent_iasio)
        # Assert:
        assert 'CHILD-ALARM' in AlarmCollection.get_all_as_dict(), 'New alarms should be created'
        assert 'PARENT-ALARM' in AlarmCollection.get_all_as_dict(), 'New alarms should be created'
        assert 'PARENT-ALARM' in AlarmCollection._get_parents('CHILD-ALARM'), \
            'The alarm core_id should be added as a parent of the dependency alarm in the collection'

    @pytest.mark.django_db
    def test_record_multiple_parent_references(self):
        """
        Test if when an alarm with dependencies is created, and the alarms in the dependencies already have another
        parent, it adds itself to the list of parents associated with the alarm in the dependencies
        """
        # Arrange:
        AlarmCollection.reset()
        timestamp = datetime.datetime.now()
        iasio_timestamp = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')
        child_iasio = {
            "value": "SET_MEDIUM",
            "productionTStamp": iasio_timestamp,
            "sentToBsdbTStamp": iasio_timestamp,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(CHILD-ALARM:IASIO)",
            "valueType": "ALARM",
            "depsFullRunningIds": []
        }
        parent_iasio_1 = {
            "value": "SET_MEDIUM",
            "productionTStamp": iasio_timestamp,
            "sentToBsdbTStamp": iasio_timestamp,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(PARENT-ALARM-1:IASIO)",
            "valueType": "ALARM",
            "depsFullRunningIds": ["(Converter-ID:CONVERTER)@(CHILD-ALARM:IASIO)"]
        }
        parent_iasio_2 = {
            "value": "SET_MEDIUM",
            "productionTStamp": iasio_timestamp,
            "sentToBsdbTStamp": iasio_timestamp,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(PARENT-ALARM-2:IASIO)",
            "valueType": "ALARM",
            "depsFullRunningIds": ["(Converter-ID:CONVERTER)@(CHILD-ALARM:IASIO)"]
        }
        AlarmCollection.add_or_update_alarm(child_iasio)
        AlarmCollection.add_or_update_alarm(parent_iasio_1)
        # Act:
        AlarmCollection.add_or_update_alarm(parent_iasio_2)
        # Assert:
        assert 'CHILD-ALARM' in AlarmCollection.get_all_as_dict(), 'Child alarm should be created'
        assert 'PARENT-ALARM-1' in AlarmCollection.get_all_as_dict(), 'Parent alarm 1 should be created'
        assert 'PARENT-ALARM-2' in AlarmCollection.get_all_as_dict(), 'Parent alarm 2 should be created'
        parents = AlarmCollection._get_parents('CHILD-ALARM')
        assert 'PARENT-ALARM-1' in parents and 'PARENT-ALARM-2' in parents, \
            'The core_id of the both parent alarms should be added as a parent of dependency alarm in the collection'

    @pytest.mark.django_db
    def test_get_dependencies_recursively(self):
        """ Test if the AlarmCollection can retrieve the list of dependencies of an alarm including itself"""
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
        AlarmCollection.add(alarm_1)
        AlarmCollection.add(alarm_2)
        AlarmCollection.add(alarm_3)
        AlarmCollection.add(alarm_4)
        AlarmCollection.add(alarm_5)
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

    @pytest.mark.django_db
    def test_get_ancestors_recursively(self):
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
        AlarmCollection.add(child)
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
        AlarmCollection.add(alarm_1)
        AlarmCollection.add(alarm_2)
        alarm_3 = Alarm(
            value=1,
            mode=7,
            validity=0,
            core_timestamp=10000,
            core_id='core_id_3',
            running_id='({}:IASIO)'.format('core_id_3'),
            dependencies=['core_id_1']
        )
        AlarmCollection.add(alarm_3)

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


class TestAlarmsCollectionAcknowledge:
    """ This class defines the test suite for the Alarms Collection acknowledge and ticket handling """

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_alarm_cycle(self):
        """ Test the changes in ack property of alarms as it changes through a cycle of values and Ack actions """
        # Arrange:
        AlarmCollection.reset()
        core_id = 'MOCK-ALARM'

        # 1. Create Alarm:
        timestamp = datetime.datetime.now()
        iasio_timestamp = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')
        iasio = {
            "value": "CLEARED",
            "productionTStamp": iasio_timestamp,
            "sentToBsdbTStamp": iasio_timestamp,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@({}:IASIO)".format(core_id),
            "valueType": "ALARM",
            "depsFullRunningIds": []
        }
        (tickets_to_create, tickets_to_clear) = AlarmCollection.add_or_update_alarm(iasio)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.ack is True, 'A new CLEARED Alarm must be acknowledged'
        assert tickets_to_create == [], 'A new Alarm in CLEARED state should not create a new ticket'
        assert tickets_to_clear == [], 'A new Alarm in CLEARED state should not clear a ticket'

        # 2. Change Alarm to SET:
        timestamp = timestamp + datetime.timedelta(seconds=1)
        iasio_timestamp = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')
        iasio = {
            "value": "SET_MEDIUM",
            "productionTStamp": iasio_timestamp,
            "sentToBsdbTStamp": iasio_timestamp,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@({}:IASIO)".format(core_id),
            "valueType": "ALARM",
            "depsFullRunningIds": []
        }
        (tickets_to_create, tickets_to_clear) = AlarmCollection.add_or_update_alarm(iasio)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.ack is False, 'When an Alarm changes to SET, it should not be acknowledged'
        assert tickets_to_create == [core_id], 'When an Alarm changes to SET, a new ticket should be created'
        assert tickets_to_clear == [], 'When an Alarm changes to SET, it should not clear a ticket'

        # 3. Acknowledge Alarm:
        await AlarmCollection.acknowledge(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.ack is True, 'When the Alarm is acknowledged, its ack status should be True'

        # 4. Alarm still SET:
        timestamp = timestamp + datetime.timedelta(seconds=1)
        iasio_timestamp = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')
        iasio = {
            "value": "SET_LOW",
            "productionTStamp": iasio_timestamp,
            "sentToBsdbTStamp": iasio_timestamp,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@({}:IASIO)".format(core_id),
            "valueType": "ALARM",
            "depsFullRunningIds": []
        }
        (tickets_to_create, tickets_to_clear) = AlarmCollection.add_or_update_alarm(iasio)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.ack is True, 'When an Alarm maintains its value, it should maintain its ack'
        assert tickets_to_create == [], 'When an Alarm maintains its value, it should not create a new ticket'
        assert tickets_to_clear == [], 'When an Alarm maintains its value, it should not clear a ticket'

        # 5. Alarm changes to CLEAR:
        timestamp = timestamp + datetime.timedelta(seconds=1)
        iasio_timestamp = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')
        iasio = {
            "value": "CLEARED",
            "productionTStamp": iasio_timestamp,
            "sentToBsdbTStamp": iasio_timestamp,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@({}:IASIO)".format(core_id),
            "valueType": "ALARM",
            "depsFullRunningIds": []
        }
        (tickets_to_create, tickets_to_clear) = AlarmCollection.add_or_update_alarm(iasio)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.ack is True, 'When an Alarm changes to CLEAR, its status should still be ack'
        assert tickets_to_create == [], 'When an Alarm has not been set again, it should not create a new ticket'
        assert tickets_to_clear == [core_id], 'When an Alarm has changed to cleared, its ticket should be cleared'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_ack_multiple_alarms(self, mocker):
        """ Test if the AlarmCollection can acknowledge multiple Alarms """
        # Arrange:
        AlarmCollection.reset([])
        iasio_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        core_ids = [
            'MOCK-ALARM1',
            'MOCK-ALARM2',
            'MOCK-ALARM3'
        ]
        iasios = [
            {
                "value": "SET_MEDIUM",
                "productionTStamp": iasio_time,
                "sentToBsdbTStamp": iasio_time,
                "mode": "OPERATIONAL",   # 5: OPERATIONAL
                "iasValidity": "RELIABLE",
                "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-ALARM1:IASIO)",
                "valueType": "ALARM"
            },
            {
                "value": "SET_MEDIUM",
                "productionTStamp": iasio_time,
                "sentToBsdbTStamp": iasio_time,
                "mode": "OPERATIONAL",   # 5: OPERATIONAL
                "iasValidity": "RELIABLE",
                "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-ALARM2:IASIO)",
                "valueType": "ALARM"
            },
            {
                "value": "SET_MEDIUM",
                "productionTStamp": iasio_time,
                "sentToBsdbTStamp": iasio_time,
                "mode": "OPERATIONAL",   # 5: OPERATIONAL
                "iasValidity": "RELIABLE",
                "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-ALARM3:IASIO)",
                "valueType": "ALARM"
            },
        ]
        for iasio in iasios:
            AlarmCollection.add_or_update_alarm(iasio)
        # Act:
        ack_alarms_ids = await AlarmCollection.acknowledge(core_ids)
        # Assert:
        retrieved_alarm_1 = AlarmCollection.get(core_ids[0])
        retrieved_alarm_2 = AlarmCollection.get(core_ids[1])
        retrieved_alarm_3 = AlarmCollection.get(core_ids[2])
        assert retrieved_alarm_1.ack is True, 'Alarm 1 should have been acknowledged'
        assert retrieved_alarm_2.ack is True, 'Alarm 2 should have been acknowledged as it was CLEAR'
        assert retrieved_alarm_3.ack is True, 'Alarm 3 should have been acknowledged'
        assert sorted(ack_alarms_ids) == sorted(core_ids), \
            'Acknowledge method did not return the list of expected ack alarms'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_recursive_ack(self):
        """ Test if the AlarmCollection can acknowledge multiple Alarms recursively """
        # Arrange:
        timestamp_1 = int(round(time.time() * 1000))
        AlarmCollection.reset([])
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
        AlarmCollection.add(alarm_1)
        AlarmCollection.add(alarm_2)
        AlarmCollection.add(alarm_3)
        AlarmCollection.add(alarm_4)
        AlarmCollection.add(alarm_5)
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
    async def test_recursive_unack(self):
        """ Test if the AlarmCollection can unacknowledge an alarms and its
        dependent alarms recursively.
        """
        # Arrange:
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
        AlarmCollection.add(alarm_1)
        AlarmCollection.add(alarm_2)
        AlarmCollection.add(alarm_3)
        AlarmCollection.add(alarm_4)
        AlarmCollection.add(alarm_5)
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
        AlarmCollection.update_alarm(retrieved_alarm_2, new_alarm_2)
        # Assert
        retrieved_alarm_1 = AlarmCollection.get(core_id_1)
        retrieved_alarm_2 = AlarmCollection.get(core_id_2)
        retrieved_alarm_3 = AlarmCollection.get(core_id_3)
        retrieved_alarm_4 = AlarmCollection.get(core_id_4)
        retrieved_alarm_5 = AlarmCollection.get(core_id_5)
        assert not retrieved_alarm_2.ack, 'The alarm_2 must be unacknowleged'
        assert retrieved_alarm_1.ack and retrieved_alarm_3.ack, \
            'The alarm_1 and its parent alarm_3 must remain acknowledged'
        assert not retrieved_alarm_4.ack, \
            'The parent of alarm_2 (alarm_4) must be unacknowleged'
        assert not retrieved_alarm_5.ack, \
            'The grandparent of alarm_2 (alarm_5) must be unacknowleged'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_new_set_alarm_ticket_is_updated_when_cleared(self):
        """ Test if a ticket is created when a new SET Alarm arrives, and if the ticket is updated to cleared_ack
        or cleared_unack states accordingly when the Alarm changes to Clear """

        # 1. Create SET Alarm:
        AlarmCollection.reset([])
        timestamp = datetime.datetime.now()
        iasio_timestamp = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')
        core_id = 'MOCK-ALARM'
        iasio = {
            "value": "SET_LOW",
            "productionTStamp": iasio_timestamp,
            "sentToBsdbTStamp": iasio_timestamp,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@({}:IASIO)".format(core_id),
            "valueType": "ALARM",
            "depsFullRunningIds": []
        }
        (tickets_to_create, tickets_to_clear) = AlarmCollection.add_or_update_alarm(iasio)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.ack is False, 'A new SET Alarm must not be acknowledged'
        assert tickets_to_create == [core_id], 'A new Alarm in SET state should create a new ticket'
        assert tickets_to_clear == [], 'A new Alarm in SET state should not clear a ticket'

        # 2. Change Alarm to CLEAR:
        timestamp = timestamp + datetime.timedelta(seconds=1)
        iasio_timestamp = timestamp.strftime('%Y-%m-%dT%H:%M:%S.%f')
        iasio = {
            "value": "CLEARED",
            "productionTStamp": iasio_timestamp,
            "sentToBsdbTStamp": iasio_timestamp,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@({}:IASIO)".format(core_id),
            "valueType": "ALARM",
            "depsFullRunningIds": []
        }
        (tickets_to_create, tickets_to_clear) = AlarmCollection.add_or_update_alarm(iasio)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.ack is False, 'When an Alarm changes to CLEARED, it should not be acknowledged'
        assert tickets_to_create == [], 'When an Alarm changes to CLEARED, a new ticket should not be created'
        assert tickets_to_clear == [core_id], 'When an Alarm changes to CLEARED, it should clear the ticket'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_create_tickets(self, mocker):
        """
        Test that AlarmCollection.create_tickets calls
        TicketConnector.create_tickets
        """
        # Arrange:
        # Mock TicketConnector.create_tickets to assert if it was called
        # and avoid calling the real function
        mocker.patch.object(TicketConnector, 'create_tickets')
        AlarmCollection.reset()
        core_id = 'MOCK-ALARM'

        # Act:
        await AlarmCollection.create_tickets(core_id)

        # Assert:
        assert TicketConnector.create_tickets.call_count == 1, \
            'The ticket was no actually created'


class TestAlarmsCollectionShelve:
    """ This class defines the test suite for the Alarms Collection shelve and registry handling """

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_alarm_shelving(self):
        """ Test if an alarm can be shelved and unshelved """
        # 1. Create Alarm:
        timestamp_1 = int(round(time.time() * 1000))
        AlarmCollection.reset([])
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
        AlarmCollection.add(alarm_1)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.shelved is False, 'A new Alarm must be unshelved'

        # 2. Shelve Alarm:
        status = await AlarmCollection.shelve(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 1, 'The status must be 1'
        assert retrieved_alarm.shelved is True, 'When an Alarm is shelved its shelved status should be True'

        # 3. Unshelve Alarm:
        status = await AlarmCollection.unshelve(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status is True, 'The status must be True'
        assert retrieved_alarm.shelved is False, 'When an Alarm is unshelved its shelved status should be False'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_forbid_alarm_shelving(self):
        """ Test if a non-shelvable alarm cannot be shelved and unshelved """
        # 1. Create Alarm:
        timestamp_1 = int(round(time.time() * 1000))
        AlarmCollection.reset([])
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
        AlarmCollection.add(alarm_1)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.shelved is False, 'A new Alarm must be unshelved'

        # 2. Shelve Alarm:
        status = await AlarmCollection.shelve(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status is -1, 'The status must be -1'
        assert retrieved_alarm.shelved is False, 'When an Alarm is not shelved its shelved status should be False'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_already_shelved_alarm(self):
        """ Test if an already shelved alarm cannot be shelved """
        # 1. Create Alarm:
        timestamp_1 = int(round(time.time() * 1000))
        AlarmCollection.reset([])
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
        AlarmCollection.add(alarm_1)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.shelved is False, 'A new Alarm must be unshelved'

        # 2. Shelve Alarm:
        status = await AlarmCollection.shelve(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 1, 'The status must be 1'
        assert retrieved_alarm.shelved is True, 'When an Alarm is shelved its shelved status should be True'

        # 3. Shelve Alarm again:
        status = await AlarmCollection.shelve(core_id)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert status == 0, 'The status must be 0'
        assert retrieved_alarm.shelved is True, 'When an Alarm is shelved its shelved status should be True'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_no_ticket_for_shelved_alarm(self, mocker):
        """ Test if tickets are not created for Alarms in shelved status """
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
        tickets_to_create = AlarmCollection.add(alarm_1)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.ack is True, 'A new CLEARED Alarm must be acknowledged'
        assert tickets_to_create == [], \
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
        notify, tickets_to_create, tickets_to_clear = AlarmCollection.update_alarm(retrieved_alarm, alarm_2)
        retrieved_alarm = AlarmCollection.get(core_id)
        assert retrieved_alarm.ack is True, 'When a shelved Alarm changes to SET, its ack should not change'
        assert tickets_to_create == [], \
            'When a shelved Alarm changes to SET, a new ticket should not be created'
#
#     @pytest.mark.django_db
#     def test_initialize(self, mocker):
#         """ Test the AlarmCollection initialization """
#         # Arrange:
#         mock_ids = [
#             'mock_alarm_1',
#             'mock_alarm_3',
#             'mock_alarm_4',
#         ]
#         mock_iasios = [
#             {
#                 "id": "mock_alarm_0",
#                 "shortDesc": "Dummy Iasio of type ALARM 0",
#                 "iasType": "ALARM",
#                 "docUrl": "http://www.alma0.cl"
#             },
#             {
#                 "id": "mock_alarm_1",
#                 "shortDesc": "Dummy Iasio of type ALARM 1",
#                 "iasType": "ALARM",
#                 "docUrl": "http://www.alma1.cl"
#             },
#             {
#                 "id": "mock_alarm_2",
#                 "shortDesc": "Dummy Iasio of type ALARM 2",
#                 "iasType": "ALARM",
#                 "docUrl": "http://www.alma2.cl"
#             },
#             {
#                 "id": "mock_alarm_3",
#                 "shortDesc": "Dummy Iasio of type ALARM 3",
#                 "iasType": "ALARM",
#                 "docUrl": "http://www.alma3.cl"
#             },
#         ]
#         expected_alarm_ids = sorted([
#             'mock_alarm_0',
#             'mock_alarm_1',
#             'mock_alarm_2',
#             'mock_alarm_3',
#             'mock_alarm_4',
#         ])
#         expected_alarm_descriptions = sorted([
#             mock_iasios[0]['shortDesc'],
#             mock_iasios[1]['shortDesc'],
#             mock_iasios[2]['shortDesc'],
#             mock_iasios[3]['shortDesc'],
#             '',
#         ])
#         expected_alarm_urls = sorted([
#             mock_iasios[0]['docUrl'],
#             mock_iasios[1]['docUrl'],
#             mock_iasios[2]['docUrl'],
#             mock_iasios[3]['docUrl'],
#             '',
#         ])
#         PanelsConnector_get_alarm_ids_of_alarm_configs = \
#             mocker.patch.object(
#                 PanelsConnector, 'get_alarm_ids_of_alarm_configs'
#             )
#
#         CdbConnector_get_iasios = mocker.patch.object(
#             CdbConnector, 'get_iasios'
#         )
#         PanelsConnector_get_alarm_ids_of_alarm_configs.return_value = mock_ids
#         CdbConnector_get_iasios.return_value = mock_iasios
#         # Act:
#         AlarmCollection.reset()
#         # Assert:
#         alarms = AlarmCollection.get_all_as_list()
#         retrieved_alarms_ids = sorted([a.core_id for a in alarms])
#         retrieved_alarms_descriptions = sorted([a.description for a in alarms])
#         retrieved_alarms_urls = sorted([a.url for a in alarms])
#         assert retrieved_alarms_ids == expected_alarm_ids
#         assert retrieved_alarms_descriptions == expected_alarm_descriptions
#         assert retrieved_alarms_urls == expected_alarm_urls
