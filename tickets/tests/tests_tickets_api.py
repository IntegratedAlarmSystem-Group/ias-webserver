import mock
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from tickets.models import Ticket, TicketStatus
from tickets.serializers import TicketSerializer


class APITestBase:

    def create_user(self, **kwargs):
        """ Creates a user with selected permissions """
        permissions = kwargs.get('permissions', [])
        username = kwargs.get('username', 'user')
        pwd = kwargs.get('password', 'pwd')
        email = 'user@user.cl'
        user = User.objects.create_user(username, password=pwd, email=email)
        for permission in permissions:
            user.user_permissions.add(permission)
        return user

    def authenticate_client_using_token(self, client, token):
        """ Authenticates a selected API Client using a related User token """
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)


class TicketsTestSetup:
    """Class to manage the common setup for testing."""

    def setTestTicketsConfig(self):
        self.ticket_unack = Ticket(alarm_id='alarm_1')
        self.ticket_unack.save()

        self.ticket_ack = Ticket(alarm_id='alarm_1')
        self.ticket_ack.save()
        self.ticket_ack.acknowledge(
            message="Ticket was acknowledged",
            user="testuser"
        )

        self.ticket_cleared_unack = Ticket(alarm_id='alarm_1')
        self.ticket_cleared_unack.save()
        self.ticket_cleared_unack.clear()

        self.ticket_other = Ticket(alarm_id='alarm_2')
        self.ticket_other.save()

        self.ticket_dependency = Ticket(alarm_id='alarm_dependency')
        self.ticket_dependency.save()

    def setupCommonUsersAndClients(self):
        """ Add unauthenticated and unauthorized users """
        self.unauthorized_user = self.create_user(
            username='user', password='123', permissions=[])
        self.unauthenticated_client = APIClient()
        self.authenticated_unauthorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_unauthorized_client,
            Token.objects.get(user__username=self.unauthorized_user.username)
        )


class RetrieveTicket(
    APITestBase, TicketsTestSetup, TestCase
):
    """Test suite to test the retrieve request"""

    def setUp(self):
        """Define the test suite setup"""
        self.setTestTicketsConfig()
        self.setupCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_ticket'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('ticket-detail', kwargs={'pk': self.ticket_unack.pk})
        return client.get(url, format='json')

    def test_api_can_retrieve_tickets_to_authorized_user(self):
        """ The api should retrieve a ticket for an authorized user """
        # Arrange:
        expected_ticket = Ticket.objects.get(pk=self.ticket_unack.pk)
        # Act:
        client = self.authenticated_authorized_client
        self.response = self.target_request_from_client(client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The server should retrieve a 200 status'
        )
        self.assertEqual(
            self.response.data['id'],
            expected_ticket.pk,
            'The server should retrieve the expected ticket'
        )

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )

    def test_api_cannot_allow_request_for_unauthorized_user(self):
        """ The request should not be allowed for an unauthorized user """
        client = self.authenticated_unauthorized_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Request not allowed for an unauthorized user"
        )


class ListTicket(
    APITestBase, TicketsTestSetup, TestCase
):
    """Test suite to test the list request"""

    def setUp(self):
        """Define the test suite setup"""
        self.setTestTicketsConfig()
        self.setupCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_ticket'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('ticket-list')
        return client.get(url, format="json")

    def test_api_can_list_tickets_to_authorized_user(self):
        """Test that the api can list the Tickets
            to an authorized user
        """
        tickets = [
            self.ticket_unack,
            self.ticket_ack,
            self.ticket_cleared_unack,
            self.ticket_other,
            self.ticket_dependency
        ]
        expected_tickets_data = [TicketSerializer(t).data for t in tickets]
        # Act:
        client = self.authenticated_authorized_client
        self.response = self.target_request_from_client(client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the tickets'
        )
        retrieved_tickets_data = self.response.data
        self.assertEqual(
            retrieved_tickets_data,
            expected_tickets_data,
            'The retrieved tickets do not match the expected ones'
        )

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )

    def test_api_cannot_allow_request_for_unauthorized_user(self):
        """ The request should not be allowed for an unauthorized user """
        client = self.authenticated_unauthorized_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Request not allowed for an unauthorized user"
        )


class FilterTicketsByAlarmAndStatus(
    APITestBase, TicketsTestSetup, TestCase
):
    """Test suite to test the retrieve request"""

    def setUp(self):
        """Define the test suite setup"""
        self.setTestTicketsConfig()
        self.setupCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_ticket'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('ticket-filters')
        data = {
            'alarm_id': 'alarm_1',
            'status': TicketStatus.get_choices_by_name()['UNACK']
        }
        return client.get(url, data, format="json")

    def test_api_can_filter_tickets_by_alarm_and_status(self):
        """ Test that the api can list the Tickets
            filtered by alarm id and status
            only for an autorized user
        """
        # check conditions for an authorized user
        expected_tickets_data = [TicketSerializer(self.ticket_unack).data]
        # Act:
        client = self.authenticated_authorized_client
        self.response = self.target_request_from_client(client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the filtered tickets'
        )
        retrieved_tickets_data = self.response.data
        self.assertEqual(
            retrieved_tickets_data,
            expected_tickets_data,
            'The retrieved filtered tickets do not match the expected ones'
        )

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )

    def test_api_cannot_allow_request_for_unauthorized_user(self):
        """ The request should not be allowed for an unauthorized user """
        client = self.authenticated_unauthorized_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Request not allowed for an unauthorized user"
        )


class FilterTicketsByAlarm(
    APITestBase, TicketsTestSetup, TestCase
):
    """Test suite to test the retrieve request"""

    def setUp(self):
        """Define the test suite setup"""
        self.setTestTicketsConfig()
        self.setupCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_ticket'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('ticket-filters')
        data = {
            'alarm_id': 'alarm_1'
        }
        return client.get(url, data, format="json")

    def test_api_can_filter_tickets_by_alarm(self):
        """ Test that the api can list the Tickets
            filtered by alarm id
            only for an authorized user
        """
        tickets = [
            self.ticket_unack,
            self.ticket_ack,
            self.ticket_cleared_unack
        ]
        # check conditions for an authenticated user
        expected_tickets_data = [TicketSerializer(t).data for t in tickets]
        # Act:
        client = self.authenticated_authorized_client
        self.response = self.target_request_from_client(client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the filtered tickets'
        )
        retrieved_tickets_data = self.response.data
        self.assertEqual(
            retrieved_tickets_data,
            expected_tickets_data,
            'The retrieved filtered tickets do not match the expected ones'
        )

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )

    def test_api_cannot_allow_request_for_unauthorized_user(self):
        """ The request should not be allowed for an unauthorized user """
        client = self.authenticated_unauthorized_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Request not allowed for an unauthorized user"
        )


class FilterTicketsByStatus(
    APITestBase, TicketsTestSetup, TestCase
):
    """Test suite to test the retrieve request"""

    def setUp(self):
        """Define the test suite setup"""
        self.setTestTicketsConfig()
        self.setupCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_ticket'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('ticket-filters')
        data = {
            'status': TicketStatus.get_choices_by_name()['UNACK']
        }
        return client.get(url, data, format="json")

    def test_api_can_filter_tickets_by_status(self):
        """ Test that the api can list the Tickets
            filtered by status
            only for an authorized user
        """
        tickets = [
            self.ticket_unack,
            self.ticket_other,
            self.ticket_dependency
        ]
        # check conditions for an authenticated user
        expected_tickets_data = [TicketSerializer(t).data for t in tickets]
        # Act:
        client = self.authenticated_authorized_client
        self.response = self.target_request_from_client(client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the filtered tickets'
        )
        retrieved_tickets_data = self.response.data
        self.assertEqual(
            retrieved_tickets_data,
            expected_tickets_data,
            'The retrieved filtered tickets do not match the expected ones'
        )

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )

    def test_api_cannot_allow_request_for_unauthorized_user(self):
        """ The request should not be allowed for an unauthorized user """
        client = self.authenticated_unauthorized_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Request not allowed for an unauthorized user"
        )


class RetrieveOldOpenTickets(
    APITestBase, TicketsTestSetup, TestCase
):
    """Test suite to test the retrieve request"""

    def setUp(self):
        """Define the test suite setup"""
        self.setTestTicketsConfig()
        self.setupCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_ticket'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('ticket-old-open-info')
        data = {
            'alarm_id': 'alarm_2'
        }
        return client.get(url, data, format="json")

    @mock.patch('tickets.connectors.AlarmConnector.get_alarm_dependencies')
    def test_api_can_retrieve_old_open_tickets_information(
        self,
        AlarmConnector_get_alarm_dependencies
    ):
        """Test that the api can retrieve cleared unack tickets information
        of an specified alarm"""
        # check conditions for authorized user
        # Arrange:
        AlarmConnector_get_alarm_dependencies.return_value = [
            'alarm_1',
            'alarm_2'
        ]
        expected_response = {
            'alarm_1': [self.ticket_cleared_unack.pk],
            'alarm_2': []
        }
        # Act:
        client = self.authenticated_authorized_client
        self.response = self.target_request_from_client(client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the tickets'
        )
        self.assertEqual(
            self.response.data,
            expected_response,
            'The retrieved information did not match with the expected one'
        )

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )

    def test_api_cannot_allow_request_for_unauthorized_user(self):
        """ The request should not be allowed for an unauthorized user """
        client = self.authenticated_unauthorized_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Request not allowed for an unauthorized user"
        )


class AcknowledgeAllTicketsByAlarm(
    APITestBase, TicketsTestSetup, TestCase
):
    """Test suite to test the acknowledge request"""

    def setUp(self):
        """Define the test suite setup"""
        self.setTestTicketsConfig()
        self.setupCommonUsersAndClients()

        self.alarms_to_ack = ['alarm_1']
        self.data = {
            'message': 'The ticket was acknowledged',
            'user': 'testuser',
            'alarms_ids': self.alarms_to_ack
        }

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='acknowledge_ticket'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('ticket-acknowledge')
        data = self.data
        return client.put(url, data, format="json")

    @mock.patch('tickets.connectors.AlarmConnector.acknowledge_alarms')
    def test_api_can_acknowledge_all_tickets_by_alarm(
        self,
        AlarmConnector_acknowledge_alarms
    ):
        """ Test that the api can ack unacknowledged tickets
            and cleared unacknowledged tickets for an alarm
            for an authorized user
        """
        # check conditions for an authorized user
        # Arrange:
        AlarmConnector_acknowledge_alarms.return_value = ['alarm_1']
        # Act:
        client = self.authenticated_authorized_client
        self.response = self.target_request_from_client(client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not answer with the correct status'
        )
        self.assertEqual(
            self.response.data,
            self.alarms_to_ack,
            'The Server did not answer with the expected ack alarms list'
        )
        acknowledged_ticket = Ticket.objects.get(pk=self.ticket_unack.pk)
        cleared_acknowledged_ticket = Ticket.objects.get(
            pk=self.ticket_cleared_unack.pk
        )
        self.assertEqual(
            acknowledged_ticket.status,
            int(TicketStatus.get_choices_by_name()['ACK']),
            'The acknowledged ticket was not correctly acknowledged'
        )
        self.assertEqual(
            cleared_acknowledged_ticket.status,
            int(TicketStatus.get_choices_by_name()['CLEARED_ACK']),
            'The acknowledged cleared ticket was not correctly acknowledged'
        )
        self.assertEqual(
            acknowledged_ticket.message, self.data['message'],
            'The acknowledged ticket message was not recorded'
        )
        self.assertEqual(
            cleared_acknowledged_ticket.message, self.data['message'],
            'The acknowledged cleared ticket message was not recorded'
        )
        self.assertNotEqual(
            acknowledged_ticket.acknowledged_at, None,
            'The acknowledged ticket datetime was not recorded'
        )
        self.assertNotEqual(
            cleared_acknowledged_ticket.acknowledged_at, None,
            'The acknowledged cleared ticket datetime was not recorded'
        )
        self.assertEqual(
            AlarmConnector_acknowledge_alarms.call_count, 1,
            'AlarmConnector.acknowledge_alarms should have been called'
        )
        AlarmConnector_acknowledge_alarms.assert_called_with(
            self.alarms_to_ack
        )

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )

    def test_api_cannot_allow_request_for_unauthorized_user(self):
        """ The request should not be allowed for an unauthorized user """
        client = self.authenticated_unauthorized_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Request not allowed for an unauthorized user"
        )


class AcknowledgeTicketsRequestAndNoMessage(
    APITestBase, TicketsTestSetup, TestCase
):
    """Test suite to test the acknowledge request"""

    def setUp(self):
        """Define the test suite setup"""
        self.setTestTicketsConfig()
        self.setupCommonUsersAndClients()

        self.alarms_to_ack = ['alarm_1']
        self.data = {
            'message': ' ',
            'user': 'testuser',
            'alarms_ids': self.alarms_to_ack
        }

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='acknowledge_ticket'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('ticket-acknowledge')
        data = self.data
        return client.put(url, data, format="json")

    @mock.patch('tickets.connectors.AlarmConnector.acknowledge_alarms')
    def test_api_can_not_acknowledge_tickets_by_alarm_without_message(
        self,
        AlarmConnector_acknowledge_alarms
    ):
        """ Test that the api
            can not ack an unacknowledged ticket with an empty message
            for an authorized user
        """
        # check conditions for an authorized user
        # Arrange:
        AlarmConnector_acknowledge_alarms.return_value = ['alarm_1']
        # Act:
        client = self.authenticated_authorized_client
        self.response = self.target_request_from_client(client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'The Server must not retrieve the filtered tickets without a valid \
            message'
        )
        acknowledged_ticket = Ticket.objects.get(pk=self.ticket_unack.pk)
        self.assertEqual(
            acknowledged_ticket.status,
            int(TicketStatus.get_choices_by_name()['UNACK']),
            'The ticket must not be acknowledged'
        )
        self.assertEqual(
            acknowledged_ticket.message, None,
            'The ticket must not be recorded with an invalid message'
        )
        self.assertEqual(
            acknowledged_ticket.acknowledged_at, None,
            'The acknowledged_at datetime must not be updated'
        )
        self.assertFalse(
            AlarmConnector_acknowledge_alarms.called,
            'The alarm connector acknowledge method should not be called if \
            message is empty'
        )

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )

    def test_api_cannot_allow_request_for_unauthorized_user(self):
        """ The request should not be allowed for an unauthorized user """
        client = self.authenticated_unauthorized_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Request not allowed for an unauthorized user"
        )


class AcknowledgeMultipleTickets(
    APITestBase, TicketsTestSetup, TestCase
):
    """Test suite to test the acknowledge request"""

    def setUp(self):
        """Define the test suite setup"""
        self.setTestTicketsConfig()
        self.setTestTicketsConfig()
        self.setupCommonUsersAndClients()

        self.alarms_to_ack = ['alarm_1', 'alarm_2']
        self.data = {
            'alarms_ids': self.alarms_to_ack,
            'user': 'testuser',
            'message': 'The ticket was acknowledged'
        }

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='acknowledge_ticket'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('ticket-acknowledge')
        data = self.data
        return client.put(url, data, format="json")

    @mock.patch('tickets.connectors.AlarmConnector.acknowledge_alarms')
    def test_api_can_acknowledge_multiple_tickets(
        self,
        AlarmConnector_acknowledge_alarms
    ):
        """ Test that the api
            can acknowledge multiple unacknowledged tickets
            for an authorized user
        """
        # check conditions for an authorized user
        # Arrange:
        AlarmConnector_acknowledge_alarms.return_value = self.alarms_to_ack
        # Act:
        client = self.authenticated_authorized_client
        self.response = self.target_request_from_client(client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The status of the response is incorrect'
        )
        self.assertEqual(
            sorted(self.response.data),
            sorted(self.alarms_to_ack),
            'The response is not as expected'
        )
        acknowledged_tickets = [
            Ticket.objects.get(pk=self.ticket_unack.pk),
            Ticket.objects.get(pk=self.ticket_other.pk)
        ]
        expected_status = int(TicketStatus.get_choices_by_name()['ACK'])
        self.assertTrue(
            acknowledged_tickets[0].status == expected_status and
            acknowledged_tickets[1].status == expected_status,
            'The tickets was not correctly acknowledged'
        )
        self.assertEqual(
            acknowledged_tickets[0].message, self.data['message'],
            'The first ticket message was not correctly recorded'
        )
        self.assertEqual(
            acknowledged_tickets[1].message, self.data['message'],
            'The second ticket message was not correctly recorded'
        )
        self.assertEqual(
            AlarmConnector_acknowledge_alarms.call_count, 1,
            'AlarmConnector.acknowledge_alarms should have been called'
        )
        call_args, call_kwargs = AlarmConnector_acknowledge_alarms.call_args
        for alarm_id in call_args[0]:
            self.assertTrue(
                alarm_id in ['alarm_1', 'alarm_2'],
                'AlarmConnector.acknowledge_alarms was not called with the \
                expected arguments'
            )

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )

    def test_api_cannot_allow_request_for_unauthorized_user(self):
        """ The request should not be allowed for an unauthorized user """
        client = self.authenticated_unauthorized_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Request not allowed for an unauthorized user"
        )


class AcknowledgeMultipleTicketsAndDependencies(
    APITestBase, TicketsTestSetup, TestCase
):
    """Test suite to test the acknowledge request"""

    def setUp(self):
        """Define the test suite setup"""
        self.setTestTicketsConfig()
        self.setupCommonUsersAndClients()

        self.alarms_to_ack = ['alarm_1', 'alarm_2']
        self.data = {
            'alarms_ids': self.alarms_to_ack,
            'user': 'testuser',
            'message': 'The ticket was acknowledged'
        }

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='acknowledge_ticket'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('ticket-acknowledge')
        data = self.data
        return client.put(url, data, format="json")

    @mock.patch('tickets.connectors.AlarmConnector.acknowledge_alarms')
    def test_api_can_acknowledge_multiple_tickets_with_dependencies(
        self,
        AlarmConnector_acknowledge_alarms
    ):
        """ Test that the api
            can acknowledge multiple unacknowledged tickets
            and their dependencies
            for an authorized user
        """
        # Arrange
        alarms_and_dependency = self.alarms_to_ack + ['alarm_dependency']
        AlarmConnector_acknowledge_alarms.return_value = alarms_and_dependency
        # Act:
        client = self.authenticated_authorized_client
        self.response = self.target_request_from_client(client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The status of the response is incorrect'
        )
        self.assertEqual(
            sorted(self.response.data),
            sorted(alarms_and_dependency),
            'The response is not as expected'
        )
        acknowledged_tickets = [
            Ticket.objects.get(pk=self.ticket_unack.pk),
            Ticket.objects.get(pk=self.ticket_other.pk),
            Ticket.objects.get(pk=self.ticket_dependency.pk)
        ]
        expected_status = int(TicketStatus.get_choices_by_name()['ACK'])
        self.assertTrue(
            acknowledged_tickets[0].status == expected_status and
            acknowledged_tickets[1].status == expected_status and
            acknowledged_tickets[2].status == expected_status,
            'The tickets was not correctly acknowledged'
        )
        self.assertEqual(
            acknowledged_tickets[0].message, self.data['message'],
            'The first ticket message was not correctly recorded'
        )
        self.assertEqual(
            acknowledged_tickets[1].message, self.data['message'],
            'The second ticket message was not correctly recorded'
        )
        self.assertEqual(
            acknowledged_tickets[2].message, self.data['message'],
            'The dependency ticket message was not correctly recorded'
        )
        self.assertEqual(
            AlarmConnector_acknowledge_alarms.call_count, 1,
            'AlarmConnector.acknowledge_alarms should have been called'
        )
        call_args, call_kwargs = AlarmConnector_acknowledge_alarms.call_args
        for alarm_id in call_args[0]:
            self.assertTrue(
                alarm_id in ['alarm_1', 'alarm_2'],
                'AlarmConnector.acknowledge_alarms was not called with the \
                expected arguments'
            )

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )

    def test_api_cannot_allow_request_for_unauthorized_user(self):
        """ The request should not be allowed for an unauthorized user """
        client = self.authenticated_unauthorized_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Request not allowed for an unauthorized user"
        )


class CreateTicketTestCase(APITestBase, TestCase):
    """Test suite to test the creation permissions of tickets using the api."""

    def setUp(self):
        """Define the test suite setup."""
        self.unauthorized_user = self.create_user(
            username='user', password='123',
            permissions=[])
        self.unauthenticated_client = APIClient()
        self.authentication_user = self.create_user(
            username='to_be_authenticated', password='123',
            permissions=[])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authentication_user.username)
        )
        self.authenticated_client = client

    def target_request_from_client(self, client):
        url = reverse('ticket-list')
        data = {
            'alarm_id': 'alarm_1',
            'message': 'Action message'
        }
        return client.post(url, data, format='json')

    def test_ticket_should_not_have_and_add_default_permission(self):
        """ Should not be permissions to add tickets using the api """
        self.assertTrue(
            'add' not in Ticket._meta.default_permissions,
            'Should not be an add permission by default for the Ticket model')

    def test_unavailable_add_ticket_permission_for_the_users(self):
        """ Should not be permissions for the users """
        self.assertEqual(
            Permission.objects.filter(codename='add_ticket').count(),
            0,
            'Should not be an add permission available for the users')

    def test_api_should_always_unallow_the_create_permission(self):
        """ Should not be allowed to add tickets using the api """
        # Arrange:
        content_type = ContentType.objects.get_for_model(Ticket)
        unexpected_add_permission = Permission.objects.create(
            content_type=content_type, codename='add_ticket')
        unexpected_user = self.create_user(
            username='unexpected_user', password='123',
            permissions=[
                unexpected_add_permission
            ])
        unexpected_client = APIClient()
        self.authenticate_client_using_token(
            unexpected_client,
            Token.objects.get(user__username=unexpected_user.username)
        )
        # Act:
        self.response = self.target_request_from_client(unexpected_client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            'The create request should not be allowed from the API'
        )

    def test_api_cannot_create_tickets_for_an_unauthenticated_user(self):
        """ Test that an unauthenticated user can not use the request """
        # Act:
        self.response = self.target_request_from_client(
            self.unauthenticated_client
        )
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            'The request should not be allowed for an unauthenticated user'
        )

    def test_api_cannot_create_tickets_for_an_authenticated_user(self):
        """ Test that an authenticated user can not use the request """
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_client
        )
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            'The request should not be allowed for an authenticated user'
        )
