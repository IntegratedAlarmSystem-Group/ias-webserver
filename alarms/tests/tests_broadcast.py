import datetime
import pytest
from freezegun import freeze_time
from channels.testing import WebsocketCommunicator
from alarms.consumers import ClientConsumer
from alarms.collections import AlarmCollection
from alarms.tests.factories import AlarmFactory
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from ias_webserver.routing import application as ias_app


class TestPeriodicBroadcastCase:
    """This class defines the test suite for periodic notification of changes
    to consumer clients"""

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
    async def test_broadcast_status(self):
        """ Test that the periodic request is sent
        and Alarms are invalidated after timeout """
        AlarmCollection.reset([])
        user = User.objects.create_user('username', password='123', email='user@user.cl')
        token = Token.objects.get(user__username=user.username)
        query_string = 'token={}'.format(token)
        # Connect:
        communicator = self.create_communicator(query_string=query_string)
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'

        observer = User.objects.create_user('observer', password='123', email='user2@user.cl')
        token = Token.objects.get(user__username=observer.username)
        query_string = 'token={}'.format(token)
        communicator_observer = self.create_communicator(query_string=query_string)
        connected_obs, subprotocol_obs = await communicator_observer.connect()
        assert connected_obs, 'The communicator was not connected'

        # Arrange:
        initial_time = datetime.datetime.now()
        with freeze_time(initial_time) as frozen_datetime:
            # create 3 valid alarms
            # and stored them as invalid in expected_alarms:
            expected_alarms_count = 3
            expected_alarms_list = []
            for k in range(expected_alarms_count):
                valid_alarm = AlarmFactory.get_valid_alarm()
                AlarmCollection.add(valid_alarm)
                alarm_dict = valid_alarm.to_dict()
                alarm_dict['validity'] = 0
                expected_alarms_list.append(alarm_dict)
            # Act:
            msg = {
                'stream': 'broadcast',
                'payload': {
                    'action': 'list'
                }
            }
            # make request 11 seconds after alarms were created:
            max_timedelta = datetime.timedelta(seconds=11)
            frozen_datetime.tick(delta=max_timedelta)
            await communicator.send_json_to(msg)
            await communicator.receive_json_from()
            response_observer = await communicator_observer.receive_json_from()

            # Assert:
            alarms_list = response_observer['payload']['alarms']
            sorted_alarms_list = sorted(alarms_list, key=lambda k: k['core_id'])
            sorted_expected_alarms_list = sorted(expected_alarms_list, key=lambda k: k['core_id'])
            assert sorted_alarms_list == sorted_expected_alarms_list, \
                'The alarms were not invalidated as expected after 10 seconds'
        # Close:
        await communicator.disconnect()
        await communicator_observer.disconnect()
