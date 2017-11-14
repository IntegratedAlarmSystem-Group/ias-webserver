from channels.test import ChannelTestCase, WSClient, apply_routes
from .factories import AlarmFactory
from ..models import Alarm, AlarmBinding
from ..consumers import AlarmDemultiplexer
from channels.routing import route


class TestAlarmsBinding(ChannelTestCase):
    """This class defines the test suite for the channels alarm binding"""

    def setUp(self):
        # Arrange:
        self.client = WSClient()
        self.client.join_group("alarms_group")

    def assert_received_alarm(self, received, alarm):
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

    def gen_aux_dict_from_object(self, obj):
        """pk
        Generate and return a dict without hidden fields and id from an Object
        """
        ans = {}
        for key in obj.__dict__:
            if key[0] != '_':
                ans[key] = obj.__dict__[key]
        return ans

    def test_outbound_create(self):
        """Test if clients are notified when an alarm is created"""
        # Act: (create an alarm)
        alarm = AlarmFactory()
        received = self.client.receive()

        # Assert payload structure
        self.assert_received_alarm(received, alarm)

        # Assert action
        self.assertEqual(
            received['payload']['action'], 'create',
            "Payload action should be 'create'"
        )

        # Assert that is nothing to receive
        self.assertIsNone(
            self.client.receive(),
            'Received unexpected message'
        )

    def test_outbound_delete(self):
        """Test if clients are notified when an alarm is deleted"""
        # Arrange:
        alarm = AlarmFactory()
        self.client.receive()

        # Act:
        Alarm.objects.filter(pk=alarm.pk).delete()
        received = self.client.receive()

        # Assert payload structure
        self.assert_received_alarm(received, alarm)

        # Assert action
        self.assertEqual(
            received['payload']['action'], 'delete',
            "Payload aalarms.alarmction should be 'delete'"
        )

        # Assert that is nothing to receive
        self.assertIsNone(
            self.client.receive(),
            'Received unexpected message'
        )

    def test_outbound_update(self):
        """Test if clients are notified when an alarm is updated"""
        # Arrange:
        alarm = AlarmFactory()
        self.client.receive()

        # Act:
        alarm = AlarmFactory.get_modified_alarm(alarm)
        alarm.save()
        received = self.client.receive()

        # Assert payload structure
        alarm_after = Alarm.objects.get(pk=alarm.pk)
        self.assert_received_alarm(received, alarm_after)

        # Assert action
        self.assertEqual(
            received['payload']['action'], 'update',
            "Payload action should be 'update'"
        )

        # Assert that is nothing to receive
        self.assertIsNone(
            self.client.receive(),
            'Received unexpected message'
        )

    def test_inbound_create(self):
        """Test if clients can create a new alarm"""
        # Arrange:
        old_count = Alarm.objects.all().count()
        alarm = AlarmFactory.build()
        alarm_dict = self.gen_aux_dict_from_object(alarm)
        alarm_dict.pop('id')
        # Act:
        with apply_routes([AlarmDemultiplexer.as_route(path='/'),
                          route("alarms", AlarmBinding.consumer)]):
            client = WSClient()
            client.send_and_consume('websocket.connect', path='/')
            client.send_and_consume('websocket.receive', path='/', text={
                'stream': 'alarms',
                'payload': {
                    'action': 'create',
                    'data': alarm_dict
                }
            })
        # Assert:
        new_count = Alarm.objects.all().count()
        self.assertEqual(old_count + 1, new_count, 'The alarm was not created')
        created_alarm = Alarm.objects.all().first()
        created_alarm_dict = self.gen_aux_dict_from_object(created_alarm)
        created_alarm_dict.pop('id')
        self.assertEqual(created_alarm_dict, alarm_dict)

    def test_inbound_update(self):
        """Test if clients can update a new alarm"""
        # Arrange:
        alarm = AlarmFactory()
        old_count = Alarm.objects.all().count()
        aux_alarm = AlarmFactory.build()
        alarm_dict = self.gen_aux_dict_from_object(aux_alarm)
        alarm_dict.pop('id')
        print('\n alarm_dict: ', alarm_dict)
        # alarm_dict['id'] = alarm.id
        # Act:
        with apply_routes([AlarmDemultiplexer.as_route(path='/'),
                          route("alarms", AlarmBinding.consumer)]):
            client = WSClient()
            client.send_and_consume('websocket.connect', path='/')
            client.send_and_consume('websocket.receive', path='/', text={
                'stream': 'alarms',
                'payload': {
                    'model': 'alarms.alarm',
                    'action': 'update',
                    'pk': alarm.pk,
                    'data': alarm_dict
                }
            })
            # client.consume('stream')
        # Assert:alarms.alarm
        new_count = Alarm.objects.all().count()
        self.assertEqual(old_count, new_count)
        updated_alarm = Alarm.objects.all().get(pk=alarm.pk)
        updated_alarm_dict = self.gen_aux_dict_from_object(updated_alarm)
        print('\n alarm: ', alarm)
        print('\n alarm_dict: ', alarm_dict)
        print('\n updated_alarm_dict: ', updated_alarm_dict)
        self.assertEqual(updated_alarm_dict, alarm_dict)



# class TestAlarmsAux(ChannelTestCase):
#     """This class defines the test suite for the channels alarm binding"""
#
#     def setUp(self):
#         # Arrange:
#         self.client = WSClient()
#         self.client.join_group("alarms_group")
#
#     def test_check_index(self):
#
#         alarm = AlarmFactory()
#
#         print(Alarm.objects.all())
#
#         client = self.client
