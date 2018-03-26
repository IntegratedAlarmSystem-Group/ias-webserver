from cdb.models import Iasio, Ias


class CdbConnector():
    """ This class defines methods to communicate the Alarm app with the CDB app
    """

    @classmethod
    def get_iasios(self, type=None):
        """ Return a list of iasios filtered by type formatted as dict """
        if type:
            iasios = Iasio.objects.filter(ias_type=type.upper())
        else:
            iasios = Iasio.objects.all()
        return [iasio.get_data() for iasio in iasios]

    @classmethod
    def get_ias(self, pk):
        """ Return the ias if exist or None if it is not. """
        ias = Ias.objects.filter(pk=pk).first()
        if ias:
            return ias.get_data()
        else:
            return None
