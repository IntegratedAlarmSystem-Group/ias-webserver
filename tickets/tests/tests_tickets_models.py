from django.test import TestCase
from tickets.models import Ticket
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
                retrieved_ticket.status, 1,
                'Ticket must be open by default'
            )
            self.assertEqual(
                retrieved_ticket.created_at, resolution_dt,
                'Ticket was not created with the correct creation timestamp'
            )
            self.assertEqual(
                retrieved_ticket.resolved_at, None,
                'When the ticket is created the resolve_at time must be none'
            )
            self.assertEqual(
                retrieved_ticket.message, None,
                'When the ticket is created the message must be none'
            )

    def test_resolve_a_ticket(self):
        """ Test if we can resolve a ticket passing it a valid message """
        # Arrange:
        ticket = Ticket(alarm_id='alarm_id')
        ticket.save()

        # Act:
        resolution_dt = timezone.now()
        with freeze_time(resolution_dt):
            response = ticket.resolve(message='This ticket was solved')
            retrieved_ticket = Ticket.objects.get(alarm_id='alarm_id')

            # Asserts:
            self.assertEqual(
                retrieved_ticket.status, 0,
                'Solved ticket status must be closed (0)'
            )
            self.assertEqual(
                retrieved_ticket.resolved_at, resolution_dt,
                'When the ticket is solved the resolve_at time must be greater \
                 than the created_at datetime'
            )
            self.assertEqual(
                retrieved_ticket.message, 'This ticket was solved',
                'When the ticket is created the message must be none'
            )
            self.assertEqual(
                response, 'solved',
                'Valid resolution is not solved correctly'
            )
