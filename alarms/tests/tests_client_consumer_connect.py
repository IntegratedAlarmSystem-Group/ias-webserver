import pytest
from channels.testing import WebsocketCommunicator
from alarms.collections import AlarmCollection
from alarms.consumers import ClientConsumer
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from ias_webserver.routing import application as ias_app


class TestConnectionToClientConsumer:
    """This class defines the test suite for the connection
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
    async def test_connection_allowed_using_a_valid_token_query_string(self):
        """Test if clients can request the connection using a token"""
        # Arrange:
        AlarmCollection.reset([])
        user = User.objects.create_user(
            'username', password='123', email='user@user.cl')
        token = Token.objects.get(user__username=user.username)
        query_string = 'token={}'.format(token)
        # Connect:
        communicator = self.create_communicator(query_string=query_string)
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Close:
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_connection_not_allowed_for_an_invalid_token(self):
        """Test the connection can not be allowed with an invalid token"""
        # Arrange:
        AlarmCollection.reset([])
        user = User.objects.create_user(
            'username', password='123', email='user@user.cl')
        token = 'mockInvalidToken'
        query_string = 'token={}'.format(token)
        # Connect:
        communicator = self.create_communicator(query_string=query_string)
        connected, subprotocol = await communicator.connect()
        assert not connected, 'Connection should not be allowed'
        # Close:
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_connection_not_allowed_without_a_token_query_string(self):
        """Test the connection can not be allowed without token data"""
        # Arrange:
        AlarmCollection.reset([])
        user = User.objects.create_user(
            'username', password='123', email='user@user.cl')
        token = Token.objects.get(user__username=user.username)
        # Connect:
        communicator = self.create_communicator(query_string=None)
        connected, subprotocol = await communicator.connect()
        # Assert:
        assert not connected, 'Connection should not be allowed'
        # Close:
        await communicator.disconnect()
