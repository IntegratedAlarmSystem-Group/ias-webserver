import datetime
import pytest
import copy
from channels.testing import WebsocketCommunicator
from alarms.models import Alarm, IASValue
from alarms.collections import AlarmCollection
from alarms.consumers import CoreConsumer


class TestCoreConsumer:
    """This class defines the test suite for the CoreConsumer"""

    def setup_method(self):
        """TestCase setup, executed before each test of the TestCase"""
        # Arrange:
        self.iasio_alarm = {
            'id': "AlarmType-ID",
            'shortDesc': "Test iasio",
            'iasType': "alarm",
            'docUrl': 'www.dummy-url.com'
        }
        self.iasio_double = {
            'id': "DoubleType-ID",
            'shortDesc': "Test iasio",
            'iasType': "double",
            'docUrl': 'www.dummy-url.com'
        }
        self.iasios = [self.iasio_alarm, self.iasio_double]

    def test_get_core_id_from(self):
        """Test if the core_id value is extracted correctly from the full
        running id field"""
        # Arrange:
        full_running_id = '(Monitored-System-ID:MONITORED_SOFTWARE_SYSTEM)@' +\
                          '(plugin-ID:PLUGIN)@(Converter-ID:CONVERTER)@' +\
                          '(AlarmType-ID:IASIO)'
        # Act:
        id = CoreConsumer.get_core_id_from(full_running_id)
        # Assert:
        assert id == 'AlarmType-ID', \
            'The core_id was not extracted correctly from the running_id'

    def test_get_templated_core_id_from(self):
        """Test if the core_id corresponding to a templated alarm is extracted
        and cleaned correctly from running id field"""
        # Arrange:
        full_running_id = '(Monitored-System-ID:MONITORED_SOFTWARE_SYSTEM)@' +\
                          '(plugin-ID:PLUGIN)@(Converter-ID:CONVERTER)@' +\
                          '(AlarmType-Ant[!#66!]:IASIO)'
        # Act:
        id = CoreConsumer.get_core_id_from(full_running_id)
        # Assert:
        assert id == 'AlarmType-Ant instance 66', \
            'The core_id was not extracted correctly from the running_id'

    def test_get_timestamp_from(self):
        """Tests if the timestamp in milliseconds is calculated correctly"""
        # Arrange:
        formatted_current_time = '2010-02-27T06:34:00.0'
        expected_timestamp = 1267252440000
        # Act:
        current_time_millis = CoreConsumer.get_timestamp_from(
                                formatted_current_time)
        # Assert:
        assert current_time_millis == expected_timestamp, \
            'The calculated timestamp in milliseconds differs from the \
            expected in more than 1 millisecond'

    def test_get_alarm_from_core_message(self):
        # Arrange:
        current_time = datetime.datetime.now()
        formatted_current_time = current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        current_time_millis = CoreConsumer.get_timestamp_from(
                                formatted_current_time)
        ID = "(S{0}:SUPERVISOR)@(d{0}:DASU)@(a{0}:ASCE)@(AlarmID{0}:IASIO)"
        msg = {
            "value": "SET_LOW",
            "pluginProductionTStamp": formatted_current_time,
            "sentToConverterTStamp": formatted_current_time,
            "receivedFromPluginTStamp": formatted_current_time,
            "convertedProductionTStamp": formatted_current_time,
            "sentToBsdbTStamp": formatted_current_time,
            "readFromBsdbTStamp": formatted_current_time,
            "dasuProductionTStamp": formatted_current_time,
            "depsFullRunningIds": [ID.format(1), ID.format(2)],
            "props": {"key1": "value1", "key2": "value2"},
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": ID.format(3),
            "valueType": "ALARM"
        }
        expected_alarm = Alarm(
            value=1,
            mode=5,
            validity=1,
            core_timestamp=current_time_millis,
            core_id=CoreConsumer.get_core_id_from(msg['fullRunningId']),
            running_id=msg['fullRunningId'],
            dependencies=['AlarmID{0}'.format(1), 'AlarmID{0}'.format(2)],
            properties={'key1': 'value1', 'key2': 'value2'},
            timestamps={
                'pluginProductionTStamp': current_time_millis,
                'sentToConverterTStamp': current_time_millis,
                'receivedFromPluginTStamp': current_time_millis,
                'convertedProductionTStamp': current_time_millis,
                'sentToBsdbTStamp': current_time_millis,
                'readFromBsdbTStamp': current_time_millis,
                'dasuProductionTStamp': current_time_millis,
            }
        )
        # Act:
        alarm = CoreConsumer.get_alarm_from_core_msg(msg)
        # Assert:
        assert alarm.to_dict() == expected_alarm.to_dict(), \
            'The alarm was not converted correctly'

    def test_get_value_from_core_message(self):
        # Arrange:
        current_time = datetime.datetime.now()
        formatted_current_time = current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        current_time_millis = CoreConsumer.get_timestamp_from(
                                formatted_current_time)
        ID = "(S{0}:SUPERVISOR)@(d{0}:DASU)@(a{0}:ASCE)@(IASIOID{0}:STRING)"
        msg = {
            "value": "SOME_VALUE",
            "readFromMonSysTStamp": formatted_current_time,
            "pluginProductionTStamp": formatted_current_time,
            "sentToConverterTStamp": formatted_current_time,
            "receivedFromPluginTStamp": formatted_current_time,
            "convertedProductionTStamp": formatted_current_time,
            "sentToBsdbTStamp": formatted_current_time,
            "readFromBsdbTStamp": formatted_current_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": ID.format(3),
            "valueType": "STRING"
        }

        expected_value = IASValue(
            value="SOME_VALUE",
            mode=5,
            validity=1,
            core_timestamp=current_time_millis,
            core_id=CoreConsumer.get_core_id_from(msg['fullRunningId']),
            running_id=msg['fullRunningId'],
            timestamps={
                'readFromMonSysTStamp': current_time_millis,
                'pluginProductionTStamp': current_time_millis,
                'sentToConverterTStamp': current_time_millis,
                'receivedFromPluginTStamp': current_time_millis,
                'convertedProductionTStamp': current_time_millis,
                'sentToBsdbTStamp': current_time_millis,
                'readFromBsdbTStamp': current_time_millis,
            }
        )
        # Act:
        value = CoreConsumer.get_value_from_core_msg(msg)
        # Assert:
        assert value.to_dict() == expected_value.to_dict(), \
            'The ias value was not converted correctly'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_create_alarm_on_dict(self, mocker):
        """ Test if the core consumer updates the Alarm in the AlarmCollection
        when a new alarm arrives """
        mocker.patch.object(AlarmCollection, '_create_ticket')
        # Connect:
        communicator = WebsocketCommunicator(CoreConsumer, "/core/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Arrange:
        AlarmCollection.reset(self.iasios)
        current_time = datetime.datetime.now()
        formatted_current_time = current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        current_time_millis = CoreConsumer.get_timestamp_from(
                                formatted_current_time)
        msg = {
            "value": "SET_MEDIUM",
            "dasuProductionTStamp": formatted_current_time,
            "sentToBsdbTStamp": formatted_current_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Monitored-System-ID:MONITORED_SOFTWARE_SYS" +
                             "TEM)@(plugin-ID:PLUGIN)@(Converter-ID:CONVER" +
                             "TER)@(AlarmType-ID:IASIO)",
            "valueType": "ALARM"
        }
        expected_alarm = Alarm(
            value=2,
            mode=5,
            validity=1,
            core_timestamp=current_time_millis,
            state_change_timestamp=current_time_millis,
            core_id=CoreConsumer.get_core_id_from(msg['fullRunningId']),
            running_id=msg['fullRunningId'],
            dependencies=[],
            properties={},
            timestamps={
                'dasuProductionTStamp': current_time_millis,
                'sentToBsdbTStamp': current_time_millis
            },
            description=self.iasio_alarm['shortDesc'],
            url=self.iasio_alarm['docUrl'],
            ack=False,
            shelved=False,
        )
        # Act:
        alarm_before_send = copy.copy(AlarmCollection.get('AlarmType-ID'))
        await communicator.send_json_to(msg)
        response = await communicator.receive_from()
        alarm_after_send = AlarmCollection.get('AlarmType-ID')
        # Assert:
        assert response == 'updated-alarm', 'The alarm was not updated'
        assert alarm_before_send.to_dict() != alarm_after_send.to_dict(), \
            'The alarm was not updated'
        assert alarm_after_send.to_dict() == expected_alarm.to_dict(), \
            'The alarm was not updated as expected, some fields are different'
        # Close:
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_create_value_on_values_dict(self, mocker):
        """ Test if the core consumer creates the IASValue in the
        AlarmCollection when a new IasValue (no alarm) arrives """
        # Connect:
        communicator = WebsocketCommunicator(CoreConsumer, "/core/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Arrange:
        AlarmCollection.reset(self.iasios)
        current_time = datetime.datetime.now()
        formatted_current_time = current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        current_time_millis = CoreConsumer.get_timestamp_from(
                                formatted_current_time)
        msg = {
            "value": "SOME_VALUE",
            "sentToBsdbTStamp": formatted_current_time,
            "readFromBsdbTStamp": formatted_current_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Monitored-System-ID:MONITORED_SOFTWARE_SYS" +
                             "TEM)@(plugin-ID:PLUGIN)@(Converter-ID:CONVER" +
                             "TER)@(IasValue-ID:IASIO)",
            "valueType": "STRING"
        }
        expected_value = IASValue(
            value="SOME_VALUE",
            mode=5,
            validity=1,
            core_timestamp=current_time_millis,
            core_id=CoreConsumer.get_core_id_from(msg['fullRunningId']),
            running_id=msg['fullRunningId'],
            timestamps={
                'sentToBsdbTStamp': current_time_millis,
                'readFromBsdbTStamp': current_time_millis
            }
        )

        # Act:
        value_before_send = copy.copy(AlarmCollection.get_value('IasValue-ID'))
        await communicator.send_json_to(msg)
        response = await communicator.receive_from()
        value_after_send = AlarmCollection.get_value('IasValue-ID')
        # Assert:
        assert response == 'created-value', 'The value was not created'
        assert value_before_send is None, \
            'The value was created before as expected'
        assert value_after_send.to_dict() == expected_value.to_dict(), \
            'The value was not created as expected, some fields are \
            different'
        # Close:
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_update_value_on_values_dict(self, mocker):
        """ Test if the core consumer updates the IASValue in the
        AlarmCollection when a new IasValue (no alarm) arrives """
        # Connect:
        communicator = WebsocketCommunicator(CoreConsumer, "/core/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'

        # Arrange:
        AlarmCollection.reset(self.iasios)
        first_time = datetime.datetime.now()
        formatted_first_time = first_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        first_msg = {
            "value": "SOME_VALUE",
            "sentToBsdbTStamp": formatted_first_time,
            "readFromBsdbTStamp": formatted_first_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Monitored-System-ID:MONITORED_SOFTWARE_SYS" +
                             "TEM)@(plugin-ID:PLUGIN)@(Converter-ID:CONVER" +
                             "TER)@(IasValue-ID:IASIO)",
            "valueType": "STRING"
        }

        await communicator.send_json_to(first_msg)
        response = await communicator.receive_from()
        assert response == 'created-value', 'The value was not created'

        # Close:
        await communicator.disconnect()

        # Connect:
        communicator = WebsocketCommunicator(CoreConsumer, "/core/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'

        # Arrange:
        second_time = datetime.datetime.now()
        formatted_second_time = second_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        second_time_millis = CoreConsumer.get_timestamp_from(
                                formatted_second_time)
        second_msg = {
            "value": "SOME_VALUE_UPDATED",
            "sentToBsdbTStamp": formatted_second_time,
            "readFromBsdbTStamp": formatted_second_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Monitored-System-ID:MONITORED_SOFTWARE_SYS" +
                             "TEM)@(plugin-ID:PLUGIN)@(Converter-ID:CONVER" +
                             "TER)@(IasValue-ID:IASIO)",
            "valueType": "STRING"
        }

        expected_value = IASValue(
            value="SOME_VALUE_UPDATED",
            mode=5,
            validity=1,
            core_timestamp=second_time_millis,
            state_change_timestamp=second_time_millis,
            core_id=CoreConsumer.get_core_id_from(second_msg['fullRunningId']),
            running_id=second_msg['fullRunningId'],
            timestamps={
                'sentToBsdbTStamp': second_time_millis,
                'readFromBsdbTStamp': second_time_millis
            }
        )

        # Act:
        value_before_send = copy.copy(AlarmCollection.get_value('IasValue-ID'))
        await communicator.send_json_to(second_msg)
        response = await communicator.receive_from()
        value_after_send = AlarmCollection.get_value('IasValue-ID')

        # Assert:
        assert response == 'updated-different', 'The value was not updated'
        assert value_before_send.to_dict() != expected_value.to_dict(), \
            'The value was not the expected before send the message'
        assert value_after_send.to_dict() == expected_value.to_dict(), \
            'The value was not created as expected, some fields are \
            different'
        # Close:
        await communicator.disconnect()
