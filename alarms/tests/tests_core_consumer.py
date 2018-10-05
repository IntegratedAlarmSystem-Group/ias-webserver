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
            'io_id': "AlarmType-ID",
            'short_desc': "Test iasio",
            'ias_type': "alarm",
            'doc_url': 'www.dummy-url.com'
        }
        self.iasio_double = {
            'io_id': "DoubleType-ID",
            'short_desc': "Test iasio",
            'ias_type': "double",
            'doc_url': 'www.dummy-url.com'
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

        expected_ias_value = IASValue(
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
        ias_value = CoreConsumer.get_value_from_core_msg(msg)
        # Assert:
        assert ias_value.to_dict() == expected_ias_value.to_dict(), \
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
            description=self.iasio_alarm['short_desc'],
            url=self.iasio_alarm['doc_url'],
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
