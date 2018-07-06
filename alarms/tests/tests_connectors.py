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

    def test_clear_ticket(self):
        """ Test that the clear_ticket function can clear a ticket """
        # Arrange:
        self.alarm_id = 'AlarmID'
        Ticket.objects.create(alarm_id=self.alarm_id)
        retrieved_ticket = Ticket.objects.get(alarm_id=self.alarm_id)
        resolution_dt = timezone.now()
        with freeze_time(resolution_dt):
            # Act:
            TicketConnector.clear_ticket(self.alarm_id)
            retrieved_ticket = Ticket.objects.get(alarm_id=self.alarm_id)

            # Assert:
            self.assertEqual(
                retrieved_ticket.status,
                int(TicketStatus.get_choices_by_name()['CLEARED_UNACK']),
                'Ticket must be cleared but unack'
            )
            self.assertEqual(
                retrieved_ticket.acknowledged_at, None,
                'Ticket should not be acknowledged'
            )
            self.assertTrue(
                retrieved_ticket.created_at < retrieved_ticket.cleared_at,
                'Ticket should be cleared after it was created'
            )
            self.assertEqual(
                retrieved_ticket.cleared_at, resolution_dt,
                'Ticket should be cleared with the correct timestamp'
            )
            self.assertEqual(
                retrieved_ticket.message,
                None,
                'When the ticket is clared but not acknowledged the message \
                must be None'
            )

    def test_check_acknowledgement(self):
        """ Test if the check_acknowledgement return true or false depending
        on if the alarm has open tickets (UNACK or CLEARED_UNACK) or not"""
        # Arrange:
        self.unack_alarm = 'unack_alarm'
        Ticket.objects.create(alarm_id=self.unack_alarm)
        self.ack_alarm = 'ack_alarm'
        ticket_ack = Ticket.objects.create(alarm_id=self.ack_alarm)
        ticket_ack.acknowledge('test')
        self.unack_cleared_alarm = 'unack_cleared_alarm'
        ticket_cleared = Ticket.objects.create(
            alarm_id=self.unack_cleared_alarm
        )
        ticket_cleared.clear()
        # Act:
        unack_result = TicketConnector.check_acknowledgement(self.unack_alarm)
        ack_result = TicketConnector.check_acknowledgement(self.ack_alarm)
        unack_cleared_result = TicketConnector.check_acknowledgement(
            self.unack_cleared_alarm
        )
        # Assert:
        self.assertEqual(
            unack_result, True,
            'The check_acknowledgement should return True when the alarm has \
            tickets with state UNACK'
        )
        self.assertEqual(
            ack_result, False,
            'The check_acknowledgement should return False when the alarm has \
            all its tickets acknowledged'
        )
        self.assertEqual(
            unack_cleared_result, True,
            'The check_acknowledgement should return True when the alarm has \
            tickets with CLEARED_UNACK'
        )
