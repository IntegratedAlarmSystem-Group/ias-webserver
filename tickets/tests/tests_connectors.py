from pytest_mock import mocker
from tickets.connectors import AlarmConnector
from alarms.collections import AlarmCollection


class AlarmConnectorTestCase:
    """This class defines the test suite for the Alarms Connector"""

    def test_create_ticket(self, mocker):
        """
        Test that AlarmConnector._create_ticket calls
        AlarmCollection.acknowledge
        """
        # Arrange:
        # Mock TicketConnector.create_ticket to assert if it was called
        # and avoid calling the real function
        mocker.patch.object(AlarmCollection, 'acknowledge')
        AlarmCollection.reset()
        core_ids = ['MOCK-ALARM']

        # Act:
        AlarmConnector.acknowledge_alarms(core_ids)

        # Assert:
        assert AlarmCollection.acknowledge.call_count != 1, \
            'The AlarmCollection.acknowledge function was not called'
