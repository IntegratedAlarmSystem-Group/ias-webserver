import datetime
import pytest
from channels.testing import WebsocketCommunicator
from alarms.models import Alarm
from alarms.collections import AlarmCollection
from alarms.consumers import CoreConsumer
from cdb.models import Iasio


class TestCoreConsumer:
    """This class defines the test suite for the CoreConsumer"""

    def setup_method(self):
        """TestCase setup, executed before each test of the TestCase"""
        # Arrange:
        self.iasio_alarm = Iasio(io_id="AlarmType-ID",
                                 short_desc="Test iasio",
                                 refresh_rate=1000,
                                 ias_type="alarm")
        self.iasio_double = Iasio(io_id="DoubleType-ID",
                                  short_desc="Test iasio",
                                  refresh_rate=1000,
                                  ias_type="double")
        self.iasios = [self.iasio_alarm, self.iasio_double]
        AlarmCollection.reset(self.iasios)

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
        msg = {
            "value": "SET",
            "dasuProductionTStamp": formatted_current_time,
            'sentToBsdbTStamp': formatted_current_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Monitored-System-ID:MONITORED_SOFTWARE_SYS" +
                             "TEM)@(plugin-ID:PLUGIN)@(Converter-ID:CONVER" +
                             "TER)@(AlarmType-ID:IASIO)",
            "valueType": "ALARM"
        }
        expected_alarm = Alarm(
            value=1,
            mode='5',
            validity='1',
            core_timestamp=current_time_millis,
            core_id=CoreConsumer.get_core_id_from(msg['fullRunningId']),
            running_id=msg['fullRunningId'],
        )
        # Act:
        alarm = CoreConsumer.get_alarm_from_core_msg(msg)
        # Assert:
        assert alarm.to_dict() == expected_alarm.to_dict(), \
            'The alarm was not converted correctly'

    @pytest.mark.asyncio
    async def test_create_alarm_on_dict(self):
        """Test if the core consumer updates the Alarm in the AlarmCollection
        when a new alarm arrived.
        """
        # Connect:
        communicator = WebsocketCommunicator(CoreConsumer, "/core/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Arrange:
        current_time = datetime.datetime.now()
        formatted_current_time = current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        current_time_millis = CoreConsumer.get_timestamp_from(
                                formatted_current_time)
        msg = {
            "value": "SET",
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
            value=1,
            mode='5',
            validity='1',
            core_timestamp=current_time_millis,
            core_id=CoreConsumer.get_core_id_from(msg['fullRunningId']),
            running_id=msg['fullRunningId'],
        )
        # Act:
        alarm_before_send = AlarmCollection.get('AlarmType-ID')
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
