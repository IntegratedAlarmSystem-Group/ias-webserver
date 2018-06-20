import pytest
from pytest_mock import mocker
from tickets.connectors import AlarmConnector
from alarms.interfaces import IAlarms


class XTestAlarmConnector:
    """This class defines the test suite for the Alarms Connector"""

    @pytest.mark.asyncio
    def test_acknowledge_alarms(self, mocker):
        """
        Test that AlarmConnector.acknowledge_alarms calls
        IAlarms.acknowledge_alarms
        """
        # Arrange:
        # Mock IAlarms.acknowledge_alarms to assert if it was called
        # and avoid calling the real function
        mocker.patch.object(IAlarms, 'acknowledge_alarms')
        core_ids = ['MOCK-ALARM']
        # Act:
        AlarmConnector.acknowledge_alarms(core_ids)
        # Assert:
        assert IAlarms.acknowledge_alarms.call_count == 1, \
            'The IAlarms.acknowledge_alarms function was not called'
        IAlarms.acknowledge_alarms.assert_called_with(core_ids)
    #
    # @pytest.mark.asyncio
    # @pytest.mark.django_db
    # def test_shelve_alarm(self, mocker):
    #     """
    #     Test that AlarmConnector.shelve_alarm calls
    #     AlarmCollection.shelve
    #     """
    #     # Arrange:
    #     # Mock AlarmCollection.shelve to assert if it was called
    #     # and avoid calling the real function
    #     mocker.patch.object(AlarmCollection, 'shelve')
    #     AlarmCollection.reset()
    #     core_id = 'MOCK-ALARM'
    #     # Act:
    #     AlarmConnector.shelve_alarm(core_id)
    #     # Assert:
    #     assert AlarmCollection.shelve.call_count == 0, \
    #         'The AlarmCollection.shelve function was not called'
    #     AlarmCollection.shelve.assert_called_with(core_id)
