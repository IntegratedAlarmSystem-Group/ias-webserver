from freezegun import freeze_time
from django.test import TestCase
from django.utils import timezone
from alarms.connectors import CdbConnector, TicketConnector
from tickets.models import Ticket, TicketStatus, ShelveRegistry


class TestCdbConnector(TestCase):
    """This class defines the test suite for the Tickets Connector"""

    def test_initialize_ias(self):
        """ Test that the initialize_ias function can read the refresh rate
        and tolerance from the CDB """
        # Arrange:
        CdbConnector.refresh_rate = 0
        CdbConnector.tolerance = 0
        old_refresh_rate = CdbConnector.refresh_rate
        old_tolerance = CdbConnector.tolerance
        # Act:
        CdbConnector.initialize_ias()
        # Assert:
        new_refresh_rate = CdbConnector.refresh_rate
        new_tolerance = CdbConnector.tolerance
        self.assertNotEqual(new_refresh_rate, old_refresh_rate)
        self.assertNotEqual(new_tolerance, old_tolerance)
        self.assertEqual(new_refresh_rate, 3000)
        self.assertEqual(new_tolerance, 1000)

    def test_read_get_iasios(self):
        """ Test that the get_iasios function can the correct iasios
        from the CDB """
        # Act:
        iasios_data = CdbConnector.get_iasios()
        # Asserts:
        expected_data = [
            {
                "id": "IASIO_DUMMY_ALARM_1",
                "shortDesc": "Dummy Iasio of tyoe ALARM",
                "iasType": "ALARM",
                "docUrl": "http://www.alma.cl"
            },
            {
                "id": "IASIO_DUMMY_ALARM_2",
                "shortDesc": "Dummy Iasio of tyoe ALARM",
                "iasType": "ALARM",
                "docUrl": "http://www.alma.cl"
            },
            {
                "id": "IASIO_DUMMY_ALARM_8",
                "shortDesc": "Dummy Iasio of tyoe ALARM",
                "iasType": "ALARM",
                "docUrl": "http://www.alma.cl"
            },
            {
                "id": "IASIO_DUMMY_TEMPLATED_1 instance 3",
                "shortDesc": "Dummy teplated Iasio 1",
                "iasType": "ALARM",
                "templateId": "template-ID1"
            },
            {
                "id": "IASIO_DUMMY_TEMPLATED_1 instance 4",
                "shortDesc": "Dummy teplated Iasio 1",
                "iasType": "ALARM",
                "templateId": "template-ID1"
            },
            {
                "id": "IASIO_DUMMY_TEMPLATED_1 instance 5",
                "shortDesc": "Dummy teplated Iasio 1",
                "iasType": "ALARM",
                "templateId": "template-ID1"
            },
            {
                "id": "IASIO_DUMMY_TEMPLATED_1 instance 6",
                "shortDesc": "Dummy teplated Iasio 1",
                "iasType": "ALARM",
                "templateId": "template-ID1"
            },
            {
                "id": "IASIO_DUMMY_TEMPLATED_1 instance 7",
                "shortDesc": "Dummy teplated Iasio 1",
                "iasType": "ALARM",
                "templateId": "template-ID1"
            },
            {
                "id": "IASIO_DUMMY_TEMPLATED_1 instance 8",
                "shortDesc": "Dummy teplated Iasio 1",
                "iasType": "ALARM",
                "templateId": "template-ID1"
            },
        ]
        self.assertEqual(
            iasios_data, expected_data,
            'The data obtained is not the expected'
        )


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
