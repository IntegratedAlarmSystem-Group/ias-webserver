from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from tickets.models import Ticket
from tickets.serializers import TicketSerializer


class TicketsApiTestCase(TestCase):
    """Test suite for the api views."""

    def setUp(self):
        # Arrange:
        """Define the test suite setup"""
        self.ticket_open = Ticket(alarm_id='alarm_1')
        self.ticket_open.save()

        self.ticket_close = Ticket(alarm_id='alarm_1')
        self.ticket_close.save()
        self.ticket_close.resolve(message="Ticket was solved")

        self.ticket_other = Ticket(alarm_id='alarm_2')
        self.ticket_other.save()

        self.client = APIClient()

    def test_api_can_retrieve_tickets(self):
        """ Test that the api can retrieve a ticket """
        # Arrange:
        expected_ticket = Ticket.objects.get(pk=self.ticket_open.pk)
        # Act:
        url = reverse('ticket-detail', kwargs={'pk': self.ticket_open.pk})
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
        tickets = [self.ticket_open, self.ticket_close, self.ticket_other]
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
        """Test that the api can list the Tickets filtered by alarm id"""
        expected_tickets_data = [TicketSerializer(self.ticket_open).data]
        # Act:
        url = reverse('ticket-filters')
        data = {
            'alarm_id': 'alarm_1',
            'status': '1'
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
        tickets = [self.ticket_open, self.ticket_close]
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
        """Test that the api can list the Tickets filtered by alarm id"""
        tickets = [self.ticket_open, self.ticket_other]
        expected_tickets_data = [TicketSerializer(t).data for t in tickets]
        # Act:
        url = reverse('ticket-filters')
        data = {
            'status': '1'
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
