import pytest
from channels.testing import WebsocketCommunicator
from alarms.collections import AlarmCollection
from alarms.tests.factories import AlarmFactory
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from alarms.models import Alarm
from ias_webserver.routing import application as ias_app


class FakeCoroutine():

    def done(self):
        return False

    def cancelled(self):
        return False


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
    async def test_update(self, mocker):
        """Test if clients are notified when an alarm is created"""
        # Arrange:
        AlarmCollection.broadcast_task = FakeCoroutine()
        AlarmCollection.notification_task = FakeCoroutine()
        AlarmCollection.reset([])
        Alarm.objects.counter_by_view = {'view': 1}
        mock_alarms_dict = self.build_alarms()
        AlarmCollection.singleton_collection = mock_alarms_dict
        AlarmCollection.alarm_changes = list(mock_alarms_dict.keys())
        # Arrange: User
        user = User.objects.create_user('username', password='123', email='user@user.cl')
        token = Token.objects.get(user__username=user.username)
        query_string = 'token={}'.format(token)
        # Connect:
        communicator = self.create_communicator(query_string=query_string)
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Act:
        await AlarmCollection.notify_observers()
        response = await communicator.receive_json_from()
        # Assert:
        expected_alarms = [alarm.to_dict() for alarm in mock_alarms_dict.values()]
        retrieved_alarms = response['payload']['alarms']
        expected_alarms = sorted(expected_alarms, key=lambda i: i['core_id'])
        retrieved_alarms = sorted(retrieved_alarms, key=lambda i: i['core_id'])
        assert response['stream'] == 'alarms', 'Incorrect stream for alarm changes notification'
        assert retrieved_alarms == expected_alarms, 'Received alarms list is different than expected'
        assert response['payload']['counters'] == {'view': 1}, 'Received counters are different than expected'
        # Close:
        await communicator.disconnect()
