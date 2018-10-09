import mock
from freezegun import freeze_time
from django.test import TestCase
from django.utils import timezone
from alarms.connectors import TicketConnector, PanelsConnector
from tickets.models import Ticket, TicketStatus, ShelveRegistry


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
                'When the ticket is clared but not acknowledged the message' +
                'must be None'
            )

    def test_check_acknowledgement(self):
        """ Test if the check_acknowledgement return true or false depending
        if the alarm has open tickets (UNACK or CLEARED_UNACK) or not
        """
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
            unack_result, False,
            'The check_acknowledgement should return False when the alarm' +
            'has tickets with state UNACK'
        )
        self.assertEqual(
            ack_result, True,
            'The check_acknowledgement should return True when the alarm' +
            'has all its tickets acknowledged'
        )
        self.assertEqual(
            unack_cleared_result, False,
            'The check_acknowledgement should return False when the alarm' +
            'has tickets with CLEARED_UNACK'
        )

    def test_check_shelve(self):
        """ Test if the check_shelve return true or false depending if the
        alarm has opened shelve registries
        """
        # Arrange:
        self.shelved_alarm = 'shelved_alarm'
        ShelveRegistry.objects.create(
            alarm_id=self.shelved_alarm,
            message='test'
        )
        self.unshelved_alarm = 'unshelved_alarm'
        shelve_registry = ShelveRegistry.objects.create(
            alarm_id=self.unshelved_alarm,
            message='test'
        )
        shelve_registry.unshelve()
        self.alarm = 'alarm'
        # Act:
        shelved_result = TicketConnector.check_shelve(self.shelved_alarm)
        unshelved_result = TicketConnector.check_shelve(self.unshelved_alarm)
        alarm_result = TicketConnector.check_shelve(self.alarm)
        # Assert:
        self.assertEqual(
            shelved_result, True,
            'The check_shelve should return True if the alarm has ' +
            'ShelveRegistries with status SHELVE'
        )
        self.assertEqual(
            unshelved_result, False,
            'The check_shelve should return False if the alarm has ' +
            'all its ShelveRegistries with status UNSHELVE'
        )
        self.assertEqual(
            alarm_result, False,
            'The check_shelve should return False if the alarm has not' +
            'related ShelveRegistries'
        )


class TestPanelsConnector(TestCase):
    """This class defines the test suite for the Tickets Connector"""

    @mock.patch('panels.interfaces.IPanels.update_antennas_configuration')
    def test_update_antennas_conf(self, IPanels_update_antennas_configuration):
        """
        Test that PanelsConnector.update_antennas_configuration calls
        IPanels.update_antennas_configuration
        """
        # Arrange:
        association = "A000:PAD0,A001:PAD1,A002:PAD2"
        # Act:
        PanelsConnector.update_antennas_configuration(association)
        # Assert:
        self.assertTrue(
            IPanels_update_antennas_configuration.called,
            'The IPanels_update_antennas_configuration function was not called'
        )
        IPanels_update_antennas_configuration.assert_called_with(association)
