import mock
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from tickets.models import Ticket, TicketStatus
from tickets.serializers import TicketSerializer


class TicketsApiTestCase(TestCase):
    """Test suite for the tickets api views."""

    def setUp(self):
        # Arrange:
        """Define the test suite setup"""
        self.ticket_unack = Ticket(alarm_id='alarm_1')
        self.ticket_unack.save()

        self.ticket_ack = Ticket(alarm_id='alarm_1')
        self.ticket_ack.save()
        self.ticket_ack.acknowledge(message="Ticket was acknowledged")

        self.ticket_cleared_unack = Ticket(alarm_id='alarm_1')
        self.ticket_cleared_unack.save()
        self.ticket_cleared_unack.clear()

        self.ticket_other = Ticket(alarm_id='alarm_2')
        self.ticket_other.save()

        self.ticket_dependency = Ticket(alarm_id='alarm_dependency')
        self.ticket_dependency.save()

        self.client = APIClient()

    def test_api_can_retrieve_tickets(self):
        """ Test that the api can retrieve a ticket """
        # Arrange:
        expected_ticket = Ticket.objects.get(pk=self.ticket_unack.pk)
        # Act:
        url = reverse('ticket-detail', kwargs={'pk': self.ticket_unack.pk})
        self.response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the ticket'
        )
        self.assertEqual(
            self.response.data,
            TicketSerializer(expected_ticket).data
        )

    def test_api_can_list_tickets(self):
        """Test that the api can list the Tickets"""
        tickets = [
            self.ticket_unack,
            self.ticket_ack,
            self.ticket_cleared_unack,
            self.ticket_other,
            self.ticket_dependency
        ]
        expected_tickets_data = [TicketSerializer(t).data for t in tickets]
        # Act:
        url = reverse('ticket-list')
        self.response = self.client.get(url, format="json")
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

    def test_api_can_filter_tickets_by_alarm_and_status(self):
        """Test that the api can list the Tickets filtered by alarm id
        and status"""
        expected_tickets_data = [TicketSerializer(self.ticket_unack).data]
        # Act:
        url = reverse('ticket-filters')
        data = {
            'alarm_id': 'alarm_1',
            'status': TicketStatus.get_choices_by_name()['UNACK']
        }
        self.response = self.client.get(url, data, format="json")
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

    def test_api_can_filter_tickets_by_alarm(self):
        """Test that the api can list the Tickets filtered by alarm id"""
        tickets = [
            self.ticket_unack,
            self.ticket_ack,
            self.ticket_cleared_unack
        ]
        expected_tickets_data = [TicketSerializer(t).data for t in tickets]
        # Act:
        url = reverse('ticket-filters')
        data = {
            'alarm_id': 'alarm_1'
        }
        self.response = self.client.get(url, data, format="json")
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

    def test_api_can_filter_tickets_by_status(self):
        """Test that the api can list the Tickets filtered by status"""
        tickets = [
            self.ticket_unack,
            self.ticket_other,
            self.ticket_dependency
        ]
        expected_tickets_data = [TicketSerializer(t).data for t in tickets]
        # Act:
        url = reverse('ticket-filters')
        data = {
            'status': TicketStatus.get_choices_by_name()['UNACK']
        }
        self.response = self.client.get(url, data, format="json")
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

    @mock.patch('tickets.connectors.AlarmConnector.acknowledge_alarms')
    def test_api_can_acknowledge_all_tickets_by_alarm(
        self,
        AlarmConnector_acknowledge_alarms
    ):
        """Test that the api can ack unacknowledged tickets and cleared
        unacknowledged tickets"""
        # Assert:
        url = reverse('ticket-acknowledge')
        alarms_to_ack = ['alarm_1']
        data = {
            'message': 'The ticket was acknowledged',
            'alarms_ids': alarms_to_ack
        }
        AlarmConnector_acknowledge_alarms.return_value = ['alarm_1']
        # Act:
        self.response = self.client.put(url, data, format="json")
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not answer with the correct status'
        )
        self.assertEqual(
            self.response.data,
            alarms_to_ack,
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
            acknowledged_ticket.message, data['message'],
            'The acknowledged ticket message was not recorded'
        )
        self.assertEqual(
            cleared_acknowledged_ticket.message, data['message'],
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
            alarms_to_ack
        )

    @mock.patch('tickets.connectors.AlarmConnector.acknowledge_alarms')
    def test_api_can_not_acknowledge_tickets_by_alarm_without_message(
        self,
        AlarmConnector_acknowledge_alarms
    ):
        """Test that the api can not ack an unacknowledged ticket with an empty
        message"""
        # Arrange:
        url = reverse('ticket-acknowledge')
        alarms_to_ack = ['alarm_1']
        data = {
            'message': ' ',
            'alarms_ids': alarms_to_ack
        }
        AlarmConnector_acknowledge_alarms.return_value = ['alarm_1']
        # Act:
        self.response = self.client.put(url, data, format="json")
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

    @mock.patch('tickets.connectors.AlarmConnector.acknowledge_alarms')
    def test_api_can_acknowledge_multiple_tickets(
        self,
        AlarmConnector_acknowledge_alarms
    ):
        """Test that the api can acknowledge multiple unacknowledged tickets"""
        # Arrange:
        url = reverse('ticket-acknowledge')
        alarms_to_ack = ['alarm_1', 'alarm_2']
        data = {
            'alarms_ids': alarms_to_ack,
            'message': 'The ticket was acknowledged'
        }
        AlarmConnector_acknowledge_alarms.return_value = alarms_to_ack
        # Act:
        self.response = self.client.put(url, data, format="json")
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The status of the response is incorrect'
        )
        self.assertEqual(
            sorted(self.response.data),
            sorted(alarms_to_ack),
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
            acknowledged_tickets[0].message, data['message'],
            'The first ticket message was not correctly recorded'
        )
        self.assertEqual(
            acknowledged_tickets[1].message, data['message'],
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

    @mock.patch('tickets.connectors.AlarmConnector.acknowledge_alarms')
    def test_api_can_acknowledge_multiple_tickets_with_dependencies(
        self,
        AlarmConnector_acknowledge_alarms
    ):
        """Test that the api can acknowledge multiple unacknowledged tickets
        and their dependencies"""
        # Arrange
        url = reverse('ticket-acknowledge')
        alarms_to_ack = ['alarm_1', 'alarm_2']
        data = {
            'alarms_ids': alarms_to_ack,
            'message': 'The ticket was acknowledged'
        }
        alarms_and_dependency = alarms_to_ack + ['alarm_dependency']
        AlarmConnector_acknowledge_alarms.return_value = alarms_and_dependency
        # Act:
        self.response = self.client.put(url, data, format="json")
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
            acknowledged_tickets[0].message, data['message'],
            'The first ticket message was not correctly recorded'
        )
        self.assertEqual(
            acknowledged_tickets[1].message, data['message'],
            'The second ticket message was not correctly recorded'
        )
        self.assertEqual(
            acknowledged_tickets[2].message, data['message'],
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

    @mock.patch('tickets.connectors.AlarmConnector.get_alarm_dependencies')
    def test_api_can_retrieve_old_open_tickets_information(
        self,
        AlarmConnector_get_alarm_dependencies
    ):
        """Test that the api can retrieve cleared unack tickets information
        of an specified alarm"""
        # Arrange:
        url = reverse('ticket-old-open-info')
        data = {
            'alarm_id': 'alarm_2'
        }
        AlarmConnector_get_alarm_dependencies.return_value = [
            'alarm_1',
            'alarm_2'
        ]
        expected_response = {
            'alarm_1': [self.ticket_cleared_unack.pk],
            'alarm_2': []
        }
        # Act:
        self.response = self.client.get(url, data, format="json")
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the tickets'
        )
        print(self.response.data)
        self.assertEqual(
            self.response.data,
            expected_response,
            'The retrieved information did not match with the expected one'
        )
