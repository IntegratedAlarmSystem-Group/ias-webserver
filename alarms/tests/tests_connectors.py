from freezegun import freeze_time
from django.test import TestCase
from django.utils import timezone
from alarms.connectors import TicketConnector
from tickets.models import Ticket, TicketStatus


class TestTicketConnector(TestCase):
    """This class defines the test suite for the Tickets Connector"""

    def test_create_ticket(self):
        """ Test that the create_ticket function can create a ticket """
        # Arrange:
        resolution_dt = timezone.now()
        self.alarm_id = 'AlarmID'
        with freeze_time(resolution_dt):
            # Act:
            TicketConnector.create_ticket(self.alarm_id)
            retrieved_ticket = Ticket.objects.get(alarm_id=self.alarm_id)

            # Assert:
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
                retrieved_ticket.message, None,
                'When the ticket is created the message must be none'
            )

    def test_close_ticket(self):
        """ Test that the close_ticket function can close a ticket """
        # Arrange:
        self.alarm_id = 'AlarmID'
        Ticket.objects.create(alarm_id=self.alarm_id)
        retrieved_ticket = Ticket.objects.get(alarm_id=self.alarm_id)
        resolution_dt = timezone.now()
        with freeze_time(resolution_dt):
            # Act:
            TicketConnector.close_ticket(self.alarm_id)
            retrieved_ticket = Ticket.objects.get(alarm_id=self.alarm_id)

            # Assert:
            self.assertEqual(
                retrieved_ticket.status,
                int(TicketStatus.get_choices_by_name()['ACK']),
                'Ticket must be closed'
            )
            self.assertTrue(
                retrieved_ticket.created_at < retrieved_ticket.acknowledged_at,
                'Ticket should be created before it is acknowledged'
            )
            self.assertEqual(
                retrieved_ticket.acknowledged_at, resolution_dt,
                'Ticket should be acknowledged wit the correct timestamp'
            )
            self.assertEqual(
                retrieved_ticket.message,
                'The alarm was cleared before it was acknowledged',
                'When the ticket is created the message must be as expected'
            )
