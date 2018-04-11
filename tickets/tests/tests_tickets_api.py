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

        self.ticket_close = Ticket(alarm_id='alarm_2')
        self.ticket_close.save()
        self.ticket_close.resolve(message="Ticket was solved")

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
