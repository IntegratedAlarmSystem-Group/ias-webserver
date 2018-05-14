import pytest
from pytest_mock import mocker
from tickets.connectors import AlarmConnector
from alarms.collections import AlarmCollection


class AlarmConnectorTestCase:
    """This class defines the test suite for the Alarms Connector"""

    @pytest.mark.asyncio
    def test_acknowledge_alarms(self, mocker):
        """
        Test that AlarmConnector.acknowledge_alarms calls
        AlarmCollection.acknowledge
        """
        # Arrange:
        # Mock AlarmCollection.acknowledge to assert if it was called
        # and avoid calling the real function
        mocker.patch.object(AlarmCollection, 'acknowledge')
        AlarmCollection.reset()
        core_ids = ['MOCK-ALARM']
        # Act:
        AlarmConnector.acknowledge_alarms(core_ids)
        # Assert:
        assert AlarmCollection.acknowledge.call_count == 1, \
            'The AlarmCollection.acknowledge function was not called'
        AlarmCollection.acknowledge.assert_called_with(core_ids)
