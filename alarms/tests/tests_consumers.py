from channels.test import ChannelTestCase, WSClient
from .factories import AlarmFactory

class TestAlarmsBinding(ChannelTestCase):
    """This class defines the test suite for the alarms binding using channels"""

    def test_ounbound_create(self):
        """Test if when an alarm is created the client receive the change"""
        client = WSClient()
        client.join_group("binding.values")

        # arrange
        alarm = AlarmFactory()

        # assert if client received something
        received = client.receive()
        self.assertIsNotNone(received)

        # assert if the received object has the correct structure
        self.assertTrue('payload' in received)
        self.assertTrue('action' in received['payload'])
        self.assertTrue('data' in received['payload'])
        self.assertTrue('core_id' in received['payload']['data'])
        self.assertTrue('value' in received['payload']['data'])

        # assert if the received object correspond to an alarm creation
        self.assertEqual(received['payload']['action'], 'create')
        self.assertEqual(received['payload']['model'], 'alarms.alarm')
        self.assertEqual(received['payload']['pk'], alarm.pk)

        # assert that is nothing to receive
        self.assertIsNone(client.receive())
        