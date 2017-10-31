from channels.test import ChannelTestCase, WSClient
from .factories import AlarmFactory


class TestAlarmsBinding(ChannelTestCase):
    """This class defines the test suite for the channels alarm binding"""

    def setup(self):
        # Arrange:
        self.client = WSClient()
        self.client.join_group("binding.alarms")

    def assert_received_alarm(self, received, alarm):
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

        # Assert if client received something
        received = self.client.receive()
        self.assertIsNotNone(received)

        # Assert payload structure
        self.assert_received_alarm(received, alarm)

        # Assert action
        self.assertEqual(received['payload']['action'], 'create')

        # Assert that is nothing to receive
        self.assertIsNone(self.client.receive())
