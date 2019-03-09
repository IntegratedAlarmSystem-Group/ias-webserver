import pytest
import copy
from channels.testing import WebsocketCommunicator
from alarms.collections import AlarmCollection
from alarms.tests.factories import AlarmFactory
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from alarms.connectors import PanelsConnector
from alarms.models import Alarm
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

    def set_mock_views_configuration(self, mocker):

        mock_alarms_views_dict = {
            "alarm_SET_MEDIUM": ["view"],
            "alarm_CLEARED": ["view"]
        }

        PanelsConnector_get_alarms_views_dict_of_alarm_configs = \
            mocker.patch.object(
                PanelsConnector, 'get_alarms_views_dict_of_alarm_configs'
            )
        PanelsConnector_get_alarms_views_dict_of_alarm_configs.return_value = \
            mock_alarms_views_dict

    def build_alarms(self):

        mock_alarms = {}

        for core_id, value in [
            ('alarm_SET_MEDIUM', 2),
            ('alarm_CLEARED', 0)
        ]:
            alarm = AlarmFactory.build()
            alarm.core_id = core_id
            alarm.views = AlarmCollection.alarms_views_dict.get(
                alarm.core_id, [])
            alarm.value = value
            if value == 0:
                assert alarm.is_set() is False
            else:
                assert alarm.is_set() is True
            assert alarm.ack is False
            mock_alarms[core_id] = alarm

        return mock_alarms

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_outbound_create(self, mocker):
        """Test if clients are notified when an alarm is created"""
        # Arrange:
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset([])
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()
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
        alarm = mock_alarms_dict['alarm_SET_MEDIUM']
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
        # Arrange:
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset([])
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()
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
        alarm = mock_alarms_dict['alarm_CLEARED']
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
        # Arrange:
        self.set_mock_views_configuration(mocker)
        AlarmCollection.reset([])
        Alarm.objects.reset_counter_by_view()
        mock_alarms_dict = self.build_alarms()
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
        alarm = mock_alarms_dict['alarm_CLEARED']
        await AlarmCollection.add_or_update_and_notify(alarm)
        response = await communicator.receive_json_from()
        counter_by_view_response = await communicator.receive_json_from()
        # Act:
        # Update the alarm replacing it with an acknowledged alarm and receive
        # the notification from the communicator
        await AlarmCollection.acknowledge(alarm.core_id)
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
