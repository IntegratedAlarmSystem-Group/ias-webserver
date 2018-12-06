import pytest
import copy
from channels.testing import WebsocketCommunicator
from alarms.consumers import ClientConsumer
from alarms.collections import AlarmCollection
from alarms.tests.factories import AlarmFactory
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from alarms.collections import AlarmCollection
from alarms.connectors import PanelsConnector

from ias_webserver.routing import application as ias_app


class TestNotificationsToClientConsumer:
    """This class defines the test suite for the notification of changes
    to the ClientConsumer"""

    def create_communicator(self, **kwargs):
        """Auxiliary method to manage a token query string authentication"""

        target_endpoint = '/stream/'
        query_string = kwargs.get('query_string', None)

        if query_string is not None:
            return WebsocketCommunicator(
                    ias_app, '{}?{}'.format(target_endpoint, query_string))
        else:
            return WebsocketCommunicator(ias_app, target_endpoint)

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_outbound_create(self, mocker):
        """Test if clients are notified when an alarm is created"""
        # Arrange: Alarm
        alarm = AlarmFactory.build()
        # Arrange: Views
        mock_view_names = ['view']
        mock_alarms_views_dict = {alarm.core_id: ['view']}
        PanelsConnector_get_names_of_views = \
            mocker.patch.object(
                PanelsConnector, 'get_names_of_views'
            )
        PanelsConnector_get_names_of_views.return_value = mock_view_names
        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict
        AlarmCollection.reset([])
        # Arrange: User
        user = User.objects.create_user(
            'username', password='123', email='user@user.cl')
        token = Token.objects.get(user__username=user.username)
        query_string = 'token={}'.format(token)
        # Connect:
        communicator = self.create_communicator(query_string=query_string)
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Act:
        await AlarmCollection.add_or_update_and_notify(alarm)
        response = await communicator.receive_json_from()
        counter_by_view_response = await communicator.receive_json_from()
        # Assert:
        assert response['payload']['action'] == 'create', \
            "Action should be 'create'"
        assert response['payload']['data'] == alarm.to_dict(), \
            'Received alarm is different than expected'
        assert counter_by_view_response['stream'] == 'counter', \
            'Missing counter notification'
        assert counter_by_view_response['payload']['data'] == {'view': 1}, \
            'Unexpected count'
        # Close:
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_outbound_update(self, mocker):
        """Test if clients are notified when an alarm is updated"""
        # Arrange: Alarm
        # Cleared alarm as fixture
        alarm = AlarmFactory.get_valid_alarm(core_id='test')
        alarm.value = 0
        # Arrange: Views
        mock_view_names = ['view']
        mock_alarms_views_dict = {alarm.core_id: ['view']}
        PanelsConnector_get_names_of_views = \
            mocker.patch.object(
                PanelsConnector, 'get_names_of_views'
            )
        PanelsConnector_get_names_of_views.return_value = mock_view_names
        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict
        AlarmCollection.reset([])
        # Arrange: User
        user = User.objects.create_user(
            'username', password='123', email='user@user.cl')
        token = Token.objects.get(user__username=user.username)
        query_string = 'token={}'.format(token)
        # Connect:
        communicator = self.create_communicator(query_string=query_string)
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Arrange:
        # Create a cleared alarm and then receive from the communicator to keep
        # clean the ClientConsumer channel
        await AlarmCollection.add_or_update_and_notify(alarm)
        response = await communicator.receive_json_from()
        counter_by_view_response = await communicator.receive_json_from()
        # Act:
        # Update the alarm replacing it with a set alarm and receive the
        # notification from the communicator
        modified_alarm = copy.deepcopy(alarm)
        modified_alarm.core_timestamp = modified_alarm.core_timestamp + 10
        modified_alarm.value = 1
        await AlarmCollection.add_or_update_and_notify(modified_alarm)
        response = await communicator.receive_json_from()
        expected_data = AlarmCollection.get(alarm.core_id).to_dict()
        counter_by_view_response = await communicator.receive_json_from()
        # Assert
        assert response['payload']['action'] == 'update', \
            "Action should be 'update'"
        response_alarm = response['payload']['data']
        assert response_alarm == expected_data, \
            'Received alarm must be equal to the alarm in the AlarmCollection'
        assert counter_by_view_response['stream'] == 'counter', \
            'Missing counter notification'
        assert counter_by_view_response['payload']['data'] == {'view': 1}, \
            'Unexpected count'
        # Close:
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_outbound_acknowledge(self, mocker):
        """Test if clients are notified when an alarm is acknowledged"""
        # Arrange: Alarm
        alarm = AlarmFactory.get_valid_alarm(core_id='test')
        alarm.value = 2
        print(alarm.__dict__)
        # Arrange: Views
        mock_view_names = ['view']
        mock_alarms_views_dict = {alarm.core_id: ['view']}

        PanelsConnector_get_names_of_views = \
            mocker.patch.object(
                PanelsConnector, 'get_names_of_views'
            )
        PanelsConnector_get_names_of_views.return_value = mock_view_names

        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict
        AlarmCollection.reset([])
        # Arrange: User
        user = User.objects.create_user(
            'username', password='123', email='user@user.cl')
        token = Token.objects.get(user__username=user.username)
        query_string = 'token={}'.format(token)
        # Connect:
        communicator = self.create_communicator(query_string=query_string)
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Arrange: Alarm
        # Create an alarm and then receive from the communicator to keep clean
        # the ClientConsumer channel
        await AlarmCollection.add_or_update_and_notify(alarm)
        response = await communicator.receive_json_from()
        counter_by_view_response = await communicator.receive_json_from()
        # Act:
        # Update the alarm replacing it with an acknowledged alarm and receive
        # the notification from the communicator
        await AlarmCollection.acknowledge('test')
        response = await communicator.receive_json_from()
        counter_by_view_response = await communicator.receive_json_from()
        # Assert
        assert response['payload']['action'] == 'update', \
            "Action should be 'update'"
        response_alarm = response['payload']['data']
        assert response_alarm == alarm.to_dict(), \
            'Received alarm is different than expected'
        assert counter_by_view_response['stream'] == 'counter', \
            'Missing counter notification'
        assert counter_by_view_response['payload']['data'] == {'view': 0}, \
            'Unexpected count'
        # Close:
        await communicator.disconnect()
