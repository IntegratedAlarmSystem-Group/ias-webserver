from cdb.models import Iasio, Ias
from ticket.models import Ticket


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
        """ Create a ticket for a given Alarm ID """
        Ticket.objects.create(alarm_id=alarm_id)
