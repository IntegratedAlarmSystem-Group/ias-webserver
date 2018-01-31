from channels.test import ChannelTestCase, WSClient, apply_routes
from .factories import AlarmFactory
from ..models import Alarm, AlarmBinding
from cdb.models import Iasio
from ..consumers import AlarmDemultiplexer, AlarmRequestConsumer, CoreConsumer
from channels.routing import route
import time


def gen_aux_dict_from_object(obj):
    """
    Generate and return a dict without hidden fields and id from an Object
    """
    ans = {}
    for key in obj.__dict__:
        if key[0] != '_' and key != 'id':
            ans[key] = obj.__dict__[key]
    return ans


class TestAlarmsStorage(ChannelTestCase):
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

    def tearDown(self):
        """TestCase teardown"""
        Iasio.objects.all().delete()
        Alarm.delete_alarms()

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

    def test_initial_alarms_creation(self):
        """Test if the alarm dictionary is populated with cdb data"""
        # Arrange:
        old_count = len(Alarm.get_alarms())
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
        Alarm.initialize_alarms()
        new_count = len(Alarm.get_alarms())
        # Assert:
        self.assertEqual(
            old_count, 0,
            'The initial dictionary of alarms is not empty'
        )
        self.assertEqual(
            new_count, 1,
            'Unexpected dictionary of alarms after initialization'
        )

    def assert_received_alarm(self, received, alarm):
        """Assert if a received message corresponds to a given alarm"""
        self.assertIsNotNone(received, 'No message received')
        self.assertTrue('payload' in received, 'No payload received')
        self.assertTrue(
            'action' in received['payload'], 'Payload does not have an action'
        )
        self.assertTrue(
            'data' in received['payload'], 'Payload does not have data'
        )
        # check model and pk according to the binding
        self.assertEqual(
            received['payload']['model'], 'alarms.alarm',
            'Payload model_label does not correspond to the Alarm model'
        )
        self.assertEqual(
            received['payload']['pk'], alarm.pk,
            'Payload pk is different from alarm.pk'
        )
        # check alarms binding fields and values
        self.assertTrue(
            'value' in received['payload']['data'],
            'Payload does not contain value field'
        )
        self.assertTrue(
            'mode' in received['payload']['data'],
            'Payload does not contain mode field'
        )
        self.assertTrue(
            'core_timestamp' in received['payload']['data'],
            'Payload does not contain core_timestamp field'
        )
        self.assertTrue(
            'core_id' in received['payload']['data'],
            'Payload does not contain core_id field'
        )
        self.assertTrue(
            'running_id' in received['payload']['data'],
            'Payload does not contain running_id field'
        )
        self.assertEqual(
            received['payload']['data']['value'], alarm.value,
            'Payload value is different from alarm.value'
        )
        self.assertEqual(
            str(received['payload']['data']['mode']), alarm.mode,
            'Payload mode is different from alarm.mode'
        )
        self.assertEqual(
            received['payload']['data']['core_timestamp'],
            alarm.core_timestamp,
            'Payload core_timestamp is different from alarm.core_timestamp'
        )
        self.assertEqual(
            received['payload']['data']['core_id'], alarm.core_id,
            'Payload core_id is different from alarm.core_id'
        )
        self.assertEqual(
            received['payload']['data']['running_id'], alarm.running_id,
            'Payload running_id is different from alarm.running_id'
        )

    def clean_replication_messages(self, client):
        for k in range(self.msg_replication_factor):
            client.receive()
