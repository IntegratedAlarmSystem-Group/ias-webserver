from django.db import models


class Ias(models.Model):
    """ Main configurations of the IAS system """

    id = models.IntegerField(null=False)
    """ Id of the IAS System """

    log_level = models.CharField(max_length=10, null=False,
                                 db_column='logLevel')
    """ Log level to be used in all the components of the IAS System """

    refresh_rate = models.IntegerField(null=False, db_column='refreshRate')
    """ Refresh Rate used by the different components of the IAS System """

    tolerance = models.IntegerField(null=False, db_column='refreshRate')
    """ Tolerance to calculate the validity of the messages """

    class Meta:
        """ Meta class of the Ias """

        db_table = 'IAS'
        """ Corresponding name of the table in the database """


class Iasio(models.Model):
    """ IASIO objects represent the monitoring points """

    io_id = models.CharField(
        max_length=64, null=False, primary_key=True, db_column='io_id'
    )
    """ ID of the IASIO """

    short_desc = models.TextField(db_column='shortDesc', max_length=256)
    """ Short description """

    ias_type = models.CharField(max_length=16, null=False, db_column='iasType')
    """ Type of the IASIO """

    def save(self, *args, **kwargs):
        """ Method that saves changes to an IASIO in the CDB """
        self.ias_type = self.ias_type.upper()
        super(Iasio, self).save(*args, **kwargs)

    class Meta:
        """ Meta class of the Iasio """

        db_table = 'IASIO'
        """ Corresponding name of the table in the database """
