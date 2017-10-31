from channels.test import ChannelTestCase, WSClient
from .factories import AlarmFactory
from ..models import Alarm


class TestAlarmsBinding(ChannelTestCase):
    """This class defines the test suite for the channels alarm binding"""

    def setUp(self):
        # Arrange:
        self.client = WSClient()
        self.client.join_group("binding.alarms")

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
            'core_id' in received['payload']['data'],
            'Payload does not contain core_id field'
        )
        self.assertTrue(
            'value' in received['payload']['data'],
            'Payload does not contain value field'
        )
        self.assertEqual(
            received['payload']['data']['core_id'], alarm.core_id,
            'Payload core_id is different from alarm.core_id'
        )
        self.assertEqual(
            received['payload']['data']['value'], alarm.value,
            'Payload value is different from alarm.value'
        )

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
            "Payload action should be 'delete'"
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
        alarm.value = (alarm.value + 1) % 2
        alarm.save()
        received = self.client.receive()

        # Assert payload structure
        self.assert_received_alarm(received, alarm)

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
