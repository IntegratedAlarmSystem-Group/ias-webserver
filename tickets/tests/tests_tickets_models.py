from django.test import TestCase
from tickets.models import Ticket, TicketStatus
from freezegun import freeze_time
from django.utils import timezone


class TicketsModelsTestCase(TestCase):

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
                retrieved_ticket.acknoledged_at, None,
                'When the ticket is created the acknoledged time must be none'
            )
            self.assertEqual(
                retrieved_ticket.message, None,
                'When the ticket is created the message must be none'
            )

    def test_acknoledge_a_ticket(self):
        """ Test if we can acknoledge a ticket passing it a valid message """
        # Arrange:
        ticket = Ticket(alarm_id='alarm_id')
        ticket.save()

        # Act:
        resolution_dt = timezone.now()
        with freeze_time(resolution_dt):
            response = ticket.acknoledge(message='This ticket was solved')
            retrieved_ticket = Ticket.objects.get(alarm_id='alarm_id')

            # Asserts:
            self.assertEqual(
                retrieved_ticket.status,
                int(TicketStatus.get_choices_by_name()['ACK']),
                'Solved ticket status must be closed (0)'
            )
            self.assertEqual(
                retrieved_ticket.acknoledged_at, resolution_dt,
                'When the ticket is solved the acknoledge_at time must be \
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