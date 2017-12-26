from channels.test import ChannelTestCase, WSClient, apply_routes
from .factories import AlarmFactory
from ..models import Alarm, AlarmBinding
from ..consumers import AlarmDemultiplexer, AlarmRequestConsumer
from channels.routing import route


def gen_aux_dict_from_object(obj):
    """
    Generate and return a dict without hidden fields and id from an Object
    """
    ans = {}
    for key in obj.__dict__:
        if key[0] != '_' and key != 'id':
            ans[key] = obj.__dict__[key]
    return ans


class TestAlarmsBinding(ChannelTestCase):
    """This class defines the test suite for the channels alarm binding"""

    def setUp(self):
        """TestCase setup"""
        # Arrange:
        self.client = WSClient()
        self.client.join_group("alarms_group")
        self.msg_replication_factor = 3

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

    def test_outbound_create(self):
        """Test if clients are notified when an alarm is created"""
        # Act: (create an alarm)
        alarm = AlarmFactory()
        received = self.client.receive()
        # clean replication messsages after creation
        self.clean_replication_messages(self.client)

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
        # clean replication messsages after creation
        self.clean_replication_messages(self.client)

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
        # clean replication messsages after creation
        self.clean_replication_messages(self.client)

        # Act:
        alarm = AlarmFactory.get_modified_alarm(alarm)
        alarm.save()
        received = self.client.receive()
        # clean replication messsages after update
        self.clean_replication_messages(self.client)

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
        alarm_dict = gen_aux_dict_from_object(alarm)
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
        self.assertEqual(
            old_count + 1, new_count, 'The alarm was not created'
        )
        created_alarm = Alarm.objects.all().first()
        created_alarm_dict = gen_aux_dict_from_object(created_alarm)
        self.assertEqual(
            created_alarm_dict, alarm_dict, 'The alarm is different'
        )

    def test_inbound_update(self):
        """Test if clients can update a new alarm"""
        # Arrange:
        alarm = AlarmFactory()
        old_count = Alarm.objects.all().count()
        aux_alarm = AlarmFactory.build()
        alarm_dict = gen_aux_dict_from_object(aux_alarm)
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
        # Assert:
        new_count = Alarm.objects.all().count()
        self.assertEqual(
            old_count, new_count, 'A new object was created or deleted'
        )
        updated_alarm = Alarm.objects.all().get(pk=alarm.pk)
        updated_alarm_dict = gen_aux_dict_from_object(updated_alarm)
        self.assertEqual(
            updated_alarm_dict, alarm_dict, 'The alarm was not updated'
        )

    def test_inbound_delete(self):
        """Test if clients can delete an alarm"""
        # Arrange:
        alarm = AlarmFactory()
        old_count = Alarm.objects.all().count()
        # Act:
        with apply_routes([AlarmDemultiplexer.as_route(path='/'),
                          route("alarms", AlarmBinding.consumer)]):
            client = WSClient()
            client.send_and_consume('websocket.connect', path='/')
            client.send_and_consume('websocket.receive', path='/', text={
                'stream': 'alarms',
                'payload': {
                    'action': 'delete',
                    'pk': alarm.pk
                }
            })
        # Assert:
        new_count = Alarm.objects.all().count()
        self.assertEqual(old_count - 1, new_count, 'The alarm was not deleted')

    def test_msg_should_be_replicated_after_alarm_creation(self):

        # Arrange
        expected_messages = 1 + self.msg_replication_factor

        # Act and assert
        alarm = AlarmFactory()  # create alarm

        for k in range(expected_messages):
            received = self.client.receive()
            self.assertNotEqual(
                received, None,
                'Expected not None message {} of {}'.format(
                    k+1, expected_messages))
            self.assertEqual(
                received['payload']['action'], 'create',
                "Payload action should be 'create'"
            )
            self.assert_received_alarm(received, alarm)

        received = self.client.receive()
        self.assertEqual(received, None, 'Unexpected message')

    def test_msg_should_be_replicated_after_alarm_update(self):

        # Arrange
        expected_messages = 1 + self.msg_replication_factor

        alarm = AlarmFactory()  # create alarm
        self.client.receive()
        # clean replication messages after creation
        self.clean_replication_messages(self.client)

        # Act and assert
        alarm = AlarmFactory.get_modified_alarm(alarm)
        alarm.save()  # update alarm
        alarm_after = Alarm.objects.get(pk=alarm.pk)

        for k in range(expected_messages):
            received = self.client.receive()
            self.assertNotEqual(
                received,
                None,
                'Expected not None message {} of {}'.format(
                    k+1,
                    expected_messages
                    ))
            self.assertEqual(
                received['payload']['action'], 'update',
                "Payload action should be 'update'"
            )
            self.assert_received_alarm(received, alarm_after)

        received = self.client.receive()
        self.assertEqual(received, None, 'Unexpected message')


class TestAlarmRequestConsumer(ChannelTestCase):
    """This class defines the test suite for the channels alarm requests"""

    def setUp(self):
        """TestCase setup"""
        # Arrange:
        self.client = WSClient()

    def test_alarms_list(self):
        """Test if clients can request and receive a list of alarms"""
        # Arrange:
        expected_alarms_count = 3
        for k in range(expected_alarms_count):
            AlarmFactory()
        # Act:
        with apply_routes([AlarmDemultiplexer.as_route(path='/'),
                          route("requests", AlarmRequestConsumer)]):
            client = WSClient()
            client.send_and_consume('websocket.connect', path='/')
            client.receive()
            client.send_and_consume('websocket.receive', path='/', text={
                'stream': 'requests',
                'payload': {
                    'action': 'list'
                }
            })
            response = client.receive()
        # Assert:
        alarms = Alarm.objects.all()
        expected_alarms_list = []
        for i, alarm in enumerate(alarms):
            expected_alarms_list.append({
                'pk': alarm.pk,
                'model': 'alarms.alarm',
                'fields': gen_aux_dict_from_object(alarm)
            })
        alarms_list = response['payload']['data']
        self.assertEqual(
            alarms_list, expected_alarms_list,
            'The received alarms are different than the alarms in the DB'
        )

    def test_unsupported_action(self):
        """Test if clients can request and receive a list of alarms"""
        # Arrange:
        # Act:
        with apply_routes([AlarmDemultiplexer.as_route(path='/'),
                          route("requests", AlarmRequestConsumer)]):
            client = WSClient()
            client.send_and_consume('websocket.connect', path='/')
            client.receive()
            client.send_and_consume('websocket.receive', path='/', text={
                'stream': 'requests',
                'payload': {
                    'action': 'other_action'
                }
            })
            response = client.receive()
        # Assert:
        expected_message = 'Unsupported action'
        response_message = response['payload']['data']
        self.assertEqual(
            response_message, expected_message,
            'The received alarms are different than the alarms in the DB'
        )


class TestCoreConsumer(ChannelTestCase):
    """This class defines the test suite for the channels core consumer"""

    def setUp(self):
        """TestCase setup"""
        # Arrange:
        self.client = WSClient()

    def test_create_alarm(self):
        """Test if core clients can create a new alarm"""
        # Arrange:
        old_count = Alarm.objects.all().count()
        msg = {
            "value": "SET",
            "tStamp": 1600,
            "mode": "OPERATIONAL",
            "id": "AlarmType-ID",
            "fullRunningId": "(Monitored-System-ID:MONITORED_SOFTWARE_SYSTEM)\
                @(plugin-ID:PLUGIN)@(Converter-ID:CONVERTER)@\
                (AlarmType-ID:IASIO)",
            "valueType": "ALARM"
        }
        expected_alarm = Alarm(
            value=1,
            mode='5',
            core_timestamp=1600,
            core_id=msg['id'],
            running_id=msg['fullRunningId'],
        )
        expected_alarm_dict = gen_aux_dict_from_object(expected_alarm)
        self.client.send_and_consume('websocket.connect', path='/core/')
        expected_response = None
        self.assertEqual(
            self.client.receive(),
            expected_response,
            'Received unexpected message'
        )

        # Act:
        self.client.send_and_consume(
            'websocket.receive', path='/core/', text=msg
        )
        # Assert:
        expected_echo_response = 'created'
        new_count = Alarm.objects.all().count()
        self.assertEqual(
            self.client.receive(),
            expected_echo_response,
            'Unexpected response.'
        )
        self.assertEqual(
            old_count + 1, new_count, 'The alarm was not created'
        )
        created_alarm = Alarm.objects.all().first()
        created_alarm_dict = gen_aux_dict_from_object(created_alarm)
        self.assertEqual(
            created_alarm_dict, expected_alarm_dict, 'The alarm is different'
        )

    def test_update_alarm(self):
        """Test if core clients can update a previously created alarm"""
        # Arrange:
        msg = {
            "value": "SET",
            "tStamp": 1600,
            "mode": "MAINTENANCE",  # 4: MAINTENANCE
            "id": "AlarmType-ID",
            "fullRunningId": "(Monitored-System-ID:MONITORED_SOFTWARE_SYSTEM)\
                @(plugin-ID:PLUGIN)@(Converter-ID:CONVERTER)@\
                (AlarmType-ID:IASIO)",
            "valueType": "ALARM"
        }
        alarm = Alarm(
            value=1,
            mode='5',  # 5: OPERATIONAL
            core_timestamp=1500,
            core_id=msg['id'],
            running_id=msg['fullRunningId'],
        )
        alarm.save()
        old_count = Alarm.objects.all().count()
        expected_alarm_dict = gen_aux_dict_from_object(alarm)
        expected_alarm_dict['mode'] = '4'  # 4: MAINTENANCE
        expected_alarm_dict['core_timestamp'] = 1600
        self.client.send_and_consume('websocket.connect', path='/core/')
        expected_response = None
        self.assertEqual(
            self.client.receive(),
            expected_response,
            'Received unexpected message'
        )

        # Act:
        self.client.send_and_consume(
            'websocket.receive', path='/core/', text=msg
        )
        # Assert:
        expected_echo_response = 'updated'
        new_count = Alarm.objects.all().count()
        self.assertEqual(
            self.client.receive(),
            expected_echo_response,
            'Unexpected response.'
        )
        self.assertEqual(
            old_count, new_count,
            'A new Alarm was created instead of updating the existing one'
        )
        created_alarm = Alarm.objects.all().first()
        created_alarm_dict = gen_aux_dict_from_object(created_alarm)
        self.assertEqual(
            created_alarm_dict, expected_alarm_dict, 'The alarm is different'
        )

    def test_update_alarm_ignored(self):
        """
        Test if core clients ignore updates of alarms if there is
        nothing different, besides core_timestamp
        """
        # Arrange:
        msg = {
            "value": "SET",
            "tStamp": 1600,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "id": "AlarmType-ID",
            "fullRunningId": "(Monitored-System-ID:MONITORED_SOFTWARE_SYSTEM)\
                @(plugin-ID:PLUGIN)@(Converter-ID:CONVERTER)@\
                (AlarmType-ID:IASIO)",
            "valueType": "ALARM"
        }

        alarm = Alarm(
            value=1,
            mode='5',  # 5: OPERATIONAL
            core_timestamp=1500,
            core_id=msg['id'],
            running_id=msg['fullRunningId'],
        )
        alarm.save()
        old_count = Alarm.objects.all().count()
        expected_alarm_dict = gen_aux_dict_from_object(alarm)
        self.client.send_and_consume('websocket.connect', path='/core/')
        expected_response = None
        self.assertEqual(
            self.client.receive(),
            expected_response,
            'Received unexpected message'
        )

        # Act:
        self.client.send_and_consume(
            'websocket.receive', path='/core/', text=msg
        )
        # Assert:
        expected_echo_response = 'ignored'
        new_count = Alarm.objects.all().count()
        self.assertEqual(
            self.client.receive(),
            expected_echo_response,
            'Unexpected response.'
        )
        self.assertEqual(
            old_count, new_count,
            'A new Alarm was created instead of updating the existing one'
        )
        created_alarm = Alarm.objects.all().first()
        created_alarm_dict = gen_aux_dict_from_object(created_alarm)
        self.assertEqual(
            created_alarm_dict, expected_alarm_dict, 'The alarm is different'
        )

    def test_ignore_non_alarms(self):
        """
        Test if core clients can ignore messages that do not correspond
        to alarms
        """
        # Arrange:
        old_count = Alarm.objects.all().count()
        msg = {
            "value": "true",
            "tStamp": 1600,
            "mode": "OPERATIONAL",
            "id": "BooleanType-ID",
            "fullRunningId": "(Monitored-System-ID:MONITORED_SOFTWARE_SYSTEM)\
                @(plugin-ID:PLUGIN)@(Converter-ID:CONVERTER)\
                @(BooleanType-ID:IASIO)",
            "valueType": "BOOLEAN"
        }
        self.client.send_and_consume('websocket.connect', path='/core/')
        expected_response = None
        self.assertEqual(
            self.client.receive(),
            expected_response,
            'Received unexpected message'
        )

        # Act:
        self.client.send_and_consume(
            'websocket.receive', path='/core/', text=msg
        )
        # Assert:
        expected_echo_response = 'ignored-non-alarm'
        new_count = Alarm.objects.all().count()
        self.assertEqual(
            self.client.receive(),
            expected_echo_response,
            'Unexpected response.'
        )
        self.assertEqual(
            old_count, new_count, 'A new alarm was created'
        )
