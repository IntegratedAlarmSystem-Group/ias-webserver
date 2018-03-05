from django.db import models


class Iasio(models.Model):
    """ IASIO objects represent the monitoring points """

    io_id = models.CharField(
        max_length=64, null=False, primary_key=True, db_column='io_id'
    )
    """ ID of the IASIO """

    short_desc = models.TextField(db_column='shortDesc', max_length=256)
    """ Short description """

    refresh_rate = models.IntegerField(null=False, db_column='refreshRate')
    """ Refresh Rate """

    ias_type = models.CharField(max_length=16, null=False, db_column='iasType')
    """ Type of the IASIO """

    def save(self, *args, **kwargs):
        """ Method that saves changes to an IASIO in the CDB """
        self.ias_type = self.ias_type.upper()
        super(Iasio, self).save(*args, **kwargs)

    @classmethod
    def get_refresh_rate(self, core_id):
        """ Return the refresh rate specified for an iasio or a default value
        if the iasio is not created in the database """
        try:
            return Iasio.objects.get(io_id=core_id).refresh_rate
        except Iasio.DoesNotExist:
            return 2000

    class Meta:
        """ Meta class of the Iasio """

        db_table = 'IASIO'
        """ Corresponding name of the table in the database """
