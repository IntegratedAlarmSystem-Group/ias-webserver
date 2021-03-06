from freezegun import freeze_time
from django.test import TestCase
from django.utils import timezone
from tickets.models import Ticket, TicketStatus


class TicketsModelsTestCase(TestCase):
    """This class defines the test suite for the Tickets model tests"""

    def test_create_ticket(self):
        """ Test if we can create a ticket"""
        resolution_dt = timezone.now()
        with freeze_time(resolution_dt):
            # Act:
            ticket = Ticket(alarm_id='alarm_id')
            ticket.save()
            retrieved_ticket = Ticket.objects.get(alarm_id='alarm_id')

            # Asserts:
            self.assertEqual(
                retrieved_ticket.status,
                int(TicketStatus.get_choices_by_name()['UNACK']),
                'Ticket must be open by default'
            )
            self.assertEqual(
                retrieved_ticket.created_at, resolution_dt,
                'Ticket was not created with the correct creation timestamp'
            )
            self.assertEqual(
                retrieved_ticket.acknowledged_at, None,
                'When the ticket is created the acknowledged time must be none'
            )
            self.assertEqual(
                retrieved_ticket.cleared_at, None,
                'When the ticket is created the cleared time must be none'
            )
            self.assertEqual(
                retrieved_ticket.message, None,
                'When the ticket is created the message must be none'
            )
            self.assertEqual(
                retrieved_ticket.user, None,
                'When the ticket is created the user must be none'
            )

    def test_acknowledge_a_ticket(self):
        """ Test if we can acknowledge a ticket passing it a valid message """
        # Arrange:
        ticket = Ticket(alarm_id='alarm_id')
        ticket.save()

        # Act:
        resolution_dt = timezone.now()
        with freeze_time(resolution_dt):
            response = ticket.acknowledge(
                user='testuser',
                message='This ticket was solved'
            )
            retrieved_ticket = Ticket.objects.get(alarm_id='alarm_id')

        # Asserts:
        self.assertEqual(
            retrieved_ticket.status,
            int(TicketStatus.get_choices_by_name()['ACK']),
            'Solved ticket status must be closed (0)'
        )
        self.assertEqual(
            retrieved_ticket.acknowledged_at, resolution_dt,
            'When the ticket is solved the acknowledge_at time must be \
            greater than the created_at datetime'
        )
        self.assertEqual(
            retrieved_ticket.message, 'This ticket was solved',
            'When the ticket is created the message must be none'
        )
        self.assertEqual(
            response, 'solved',
            'Valid resolution is not solved correctly'
        )
        self.assertEqual(
            retrieved_ticket.user, 'testuser',
            'The user saved is not the expected one'
        )
