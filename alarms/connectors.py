from cdb.models import Iasio, Ias
from tickets.models import Ticket, TicketStatus


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
        if type:
            iasios = Iasio.objects.filter(ias_type=type.upper())
        else:
            iasios = Iasio.objects.all()
        return [iasio.get_data() for iasio in iasios]

    @classmethod
    def initialize_ias(self, pk):
        """ Return the ias if exist or None if it is not. """
        ias = Ias.objects.filter(pk=pk).first()
        if ias:
            data = ias.get_data()
            self.refresh_rate = data['refresh_rate']*1000
            self.tolerance = data['tolerance']*1000
        else:
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

        return True if ticket else False

    @classmethod
    def check_shelving(self, alarm_id):
        """
        Check if the alarm is shelved.

        Args:
            alarm_id (string): ID of the Alarm
        Returns:
            (bolean): true if the alarm is acknowledged otherwise false
        """
        return True
