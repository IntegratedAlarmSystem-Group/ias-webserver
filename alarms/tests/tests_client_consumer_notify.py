import pytest
import copy
from channels.testing import WebsocketCommunicator
from alarms.consumers import ClientConsumer
from alarms.collections import AlarmCollection
from alarms.tests.factories import AlarmFactory


class TestNotificationsToClientConsumer:
    """This class defines the test suite for the notification of changes
    to the ClientConsumer"""

    def setup_method(self):
        """TestCase setup, executed before each test of the TestCase"""
        # Arrange:
        AlarmCollection.reset([])

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_outbound_create(self):
        """Test if clients are notified when an alarm is created"""
        # Connect:
        communicator = WebsocketCommunicator(ClientConsumer, "/stream/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Act:
        alarm = AlarmFactory.build()
        await AlarmCollection.add_or_update_and_notify(alarm)
        response = await communicator.receive_json_from()
        # Assert:
        assert response['payload']['action'] == 'create', \
            "Action should be 'create'"
        assert response['payload']['data'] == alarm.to_dict(), \
            'Received alarm is different than expected'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_outbound_update(self):
        """Test if clients are notified when an alarm is updated"""
        # Connect:
        communicator = WebsocketCommunicator(ClientConsumer, "/stream/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'

        # Arrange:
        # Create a cleared alarm and then receive from the communicator to keep
        # clean the ClientConsumer channel
        alarm = AlarmFactory.get_valid_alarm(core_id='test')
        alarm.value = 0
        await AlarmCollection.add_or_update_and_notify(alarm)
        response = await communicator.receive_json_from()

        # Act:
        # Update the alarm replacing it with a set alarm and receive the
        # notification from the communicator
        modified_alarm = copy.deepcopy(alarm)
        modified_alarm.core_timestamp = modified_alarm.core_timestamp + 10
        modified_alarm.value = 1
        await AlarmCollection.add_or_update_and_notify(modified_alarm)
        response = await communicator.receive_json_from()
        expected_data = AlarmCollection.get(alarm.core_id).to_dict()

        # Assert
        assert response['payload']['action'] == 'update', \
            "Action should be 'update'"
        response_alarm = response['payload']['data']
        assert response_alarm == expected_data, \
            'Received alarm must be equal to the alarm in the AlarmCollection'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_outbound_acknowledge(self):
        """Test if clients are notified when an alarm is acknowledged"""
        # Connect:
        communicator = WebsocketCommunicator(ClientConsumer, "/stream/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Arrange:
        # Create an alarm and then receive from the communicator to keep clean
        # the ClientConsumer channel
        alarm = AlarmFactory.get_valid_alarm(core_id='test')
        await AlarmCollection.add_or_update_and_notify(alarm)
        response = await communicator.receive_json_from()
        # Act:
        # Update the alarm replacing it with an acknowledged alarm and receive
        # the notification from the communicator
        await AlarmCollection.acknowledge('test')
        response = await communicator.receive_json_from()
        # Assert
        assert response['payload']['action'] == 'update', \
            "Action should be 'update'"
        response_alarm = response['payload']['data']
        assert response_alarm == alarm.to_dict(), \
            'Received alarm is different than expected'

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_outbound_delete(self):
        """Test if clients are notified when an alarm is deleted"""
        # Connect:
        communicator = WebsocketCommunicator(ClientConsumer, "/stream/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Arrange:
        # Create an alarm and then receive from the communicator to keep clean
        # the ClientConsumer channel
        alarm = AlarmFactory.get_valid_alarm(core_id='test')
        await AlarmCollection.add_or_update_and_notify(alarm)
        response = await communicator.receive_json_from()
        # Act:
        # Update the alarm replacing it with an invalid alarm and receive the
        # notification from the communicator
        await AlarmCollection.delete_and_notify(alarm)
        response = await communicator.receive_json_from()

        # Assert action
        assert response['payload']['action'] == 'delete', \
            "Payload action should be 'delete'"
