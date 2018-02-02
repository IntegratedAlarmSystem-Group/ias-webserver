from channels.test import ChannelTestCase, WSClient, apply_routes
from channels.routing import route
from alarms.models import Alarm
from alarms.collections import AlarmCollection
from alarms.consumers import CoreConsumer
from cdb.models import Iasio
import time


class TestCoreConsumer(ChannelTestCase):
    """This class defines the alarm storage in a dictionary"""

    def setUp(self):
        """TestCase setup"""
        self.client = WSClient()
        self.client.join_group("alarms_group")
        self.msg_replication_factor = 3
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
        AlarmCollection.reset()

    def tearDown(self):
        """TestCase teardown"""
        Iasio.objects.all().delete()

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
        self.assertEqual(id, 'AlarmType-ID')

    def test_get_alarm_from_core_message(self):
        # Arrange:
        current_time_millis = int(round(time.time() * 1000))
        msg = {
            "value": "SET",
            "tStamp": current_time_millis,
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
        self.assertEqual(
            alarm.to_dict(), expected_alarm.to_dict(), 
            'The alarm was not converted correctly'
        )

    def test_create_alarm_on_dict(self):
        """Test if the core consumer updates the Alarm in the AlarmCollection
        when a new alarm arrived.
        """
        # Arrange:
        current_time_millis = int(round(time.time() * 1000))
        msg = {
            "value": "SET",
            "tStamp": current_time_millis,
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
        alarm_before_send = AlarmCollection.get_alarm('AlarmType-ID')
        self.client.send_and_consume(
            'websocket.receive', path='/core/', text=msg
        )
        alarm_after_send = AlarmCollection.get_alarm('AlarmType-ID')
        # Assert:
        self.assertNotEqual(
            alarm_before_send.to_dict(), alarm_after_send.to_dict(),
            'The alarm was not updated'
        )
        self.assertEqual(
            alarm_after_send.to_dict(), expected_alarm.to_dict(),
            'The alarm was not updated as expected, some fields are different'
        )
