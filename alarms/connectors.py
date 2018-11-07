import logging
from cdb.readers import CdbReader
from tickets.models import Ticket, TicketStatus
from tickets.models import ShelveRegistry, ShelveRegistryStatus
from panels.interfaces import IPanels

logger = logging.getLogger(__name__)


class CdbConnector():
    """ This class defines methods to communicate the Alarm app with the CDB app
    """

    refresh_rate = 3000
    """ refreshrate in milliseconds defined to be used to calculate the
    validity of alarms """

    tolerance = 1000
    """ Tolerance in milliseconds defined to be used as error margin for the
    calculation of validity"""

    @classmethod
    def get_iasios(self, type=None):
        """ Return a list of iasios filtered by type formatted as dict """
        return CdbReader.read_alarm_iasios()

    @classmethod
    def initialize_ias(self, pk=0):
        """ Return the ias if exist or None if it is not. """
        data = CdbReader.read_ias()
        if data and "refreshRate" in data and "tolerance" in data:
            self.refresh_rate = int(data['refreshRate'])*1000
            self.tolerance = int(data['tolerance'])*1000
            logger.info(
                'cdb initialized with refresh_rate %d ms and tolerance %d ms',
                self.refresh_rate, self.tolerance)
        else:
            logger.warning('there is not config data to read')
            return None


class TicketConnector():
    """
    This class defines methods to communicate the Alarm app with the Ticket app
    """

    @classmethod
    def create_ticket(self, alarm_id):
        """
        Create a ticket for a given Alarm ID

        Args:
            alarm_id (string): ID of the Alarm associated to the ticket
        """
        Ticket.objects.create(alarm_id=alarm_id)

    @classmethod
    def clear_ticket(self, alarm_id):
        """
        Closes a ticket for a given Alarm ID

        Args:
            alarm_id (string): ID of the Alarm associated to the ticket
        """
        queryset = Ticket.objects.filter(alarm_id=alarm_id)
        queryset = queryset.filter(
            status=int(TicketStatus.get_choices_by_name()['UNACK'])
        )
        for ticket in queryset:
            ticket.clear()
        logger.debug(
            '%d ack tickets related to alarm %s were closed',
            len(queryset), alarm_id)

    @classmethod
    def check_acknowledgement(self, alarm_id):
        """
        Check if the alarm has pending acknowledgements.

        Args:
            alarm_id (string): ID of the Alarm
        Returns:
            (bolean): true if the alarm is acknowledged otherwise false
        """
        unack_statuses = [
            int(TicketStatus.get_choices_by_name()['UNACK']),
            int(TicketStatus.get_choices_by_name()['CLEARED_UNACK'])
        ]
        ticket = Ticket.objects.filter(
            alarm_id=alarm_id,
            status__in=unack_statuses
        ).first()
        return False if ticket else True

    @classmethod
    def check_shelve(self, alarm_id):
        """
        Check if the alarm is shelved.

        Args:
            alarm_id (string): ID of the Alarm
        Returns:
            (bolean): true if the alarm is shelved otherwise false
        """
        registry = ShelveRegistry.objects.filter(
            alarm_id=alarm_id,
            status=int(ShelveRegistryStatus.get_choices_by_name()['SHELVED'])
        ).first()
        return True if registry else False


class PanelsConnector():
        """
        This class defines methods to communicate the Alarm app with the Panels
        app
        """

        @classmethod
        def update_antennas_configuration(self, antennas_pads_association):
            """
            Updates the antennas pad association in the panels configuration

            Args:
                antennas_pads_association (String): Association between
                antennas and pads got from ias core value Array-AntennasToPads
            """
            IPanels.update_antennas_configuration(antennas_pads_association)

        @classmethod
        def get_alarm_ids_of_alarm_configs(self):
            """
            Returns a list with the ids (alarm_id) of all the AlarmConfigs

            Returns:
                (list): the list of alarm ids
            """
            return IPanels.get_alarm_ids_of_alarm_configs()
