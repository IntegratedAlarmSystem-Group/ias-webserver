import mock
from django.test import TestCase
from tickets.connectors import AlarmConnector
from alarms.collections import AlarmCollection


class AlarmConnectorTestCase(TestCase):
    """This class defines the test suite for the Alarms Connector"""

    @mock.patch('alarms.collections.AlarmCollection.acknowledge')
    def test_acknowledge_alarms(self, acknowledge_mock):
        """
        Test that AlarmConnector.acknowledge_alarms calls
        AlarmCollection.acknowledge
        """
        # Arrange:
        # Mock TicketConnector.create_ticket to assert if it was called
        # and avoid calling the real function
        AlarmCollection.reset()
        core_ids = ['MOCK-ALARM']
        # Act:
        AlarmConnector.acknowledge_alarms(core_ids)
        # Assert:
        assert acknowledge_mock.call_count == 1, \
            'The AlarmCollection.acknowledge function was not called'
        acknowledge_mock.assert_called_with(core_ids)
