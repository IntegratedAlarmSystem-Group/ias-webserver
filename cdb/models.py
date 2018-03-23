from django.db import models


class Property(models.Model):
    """ Available java properties to be used in the IAS System """

    id = models.IntegerField(null=False, primary_key=True)
    """ Id of the property """

    name = models.CharField(max_length=255, null=False)
    """ Name of the property """

    value = models.CharField(max_length=255, null=False)
    """ Value of the property """

    class Meta:
        """ Meta class of the Property """

        db_table = 'PROPERTY'
        """ Corresponding name of the table in the database """

    def __str__(self):
        """Return a human readable representation of the model instance."""
        return "{}".format(self.name)

    def get_data(self):
        return {
            'name': self.name,
            'value': self.value
        }


class Ias(models.Model):
    """ Main configurations of the IAS system """

    id = models.IntegerField(null=False, primary_key=True)
    """ Id of the IAS System """

    log_level = models.CharField(max_length=10, null=False,
                                 db_column='logLevel')
    """ Log level to be used in all the components of the IAS System """

    refresh_rate = models.IntegerField(null=False, db_column='refreshRate')
    """ Refresh Rate used by the different components of the IAS System """

    tolerance = models.IntegerField(null=False)
    """ Tolerance to calculate the validity of the messages """

    properties = models.ManyToManyField(Property, db_table='IAS_PROPERTY')
    # properties = models.ManyToManyField(Property, through='Ias_Property')
    """ General properties of the Ias System """

    def save(self, *args, **kwargs):
        """ Method that saves changes to an IASIO in the CDB """
        self.log_level = self.log_level.upper()
        self.refresh_rate = self.refresh_rate * 1000
        self.tolerance = self.tolerance * 1000
        super(Ias, self).save(*args, **kwargs)

    class Meta:
        """ Meta class of the Ias """

        db_table = 'IAS'
        """ Corresponding name of the table in the database """

    def get_data(self):
        properties = [prop.get_data() for prop in self.properties.all()]
        return {
            'log_level': self.log_level,
            'refresh_rate': self.refresh_rate,
            'tolerance': self.tolerance,
            'properties': properties
        }

# Other option to specify the names of the columns in the relation table.
# TODO: Find a way to define a composite primary_key without the creation
# of another pk column to be consistent with the core CDB structure.
#
# class Ias_Property(models.Model):
#     """ Many to Many relation between Ias and Properties """
#
#     ias_id = models.ForeignKey(Ias, on_delete=models.CASCADE,
#                                db_column='Ias_id')
#     property_id = models.ForeignKey(Property, on_delete=models.CASCADE,
#                                     db_column='props_id')
#
#     class Meta:
#         """ Meta class of the IAS Property relation """
#
#         db_table = 'IAS_PROPERTY'
#
#         unique_together = (('ias_id', 'property_id'))


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

    def get_data(self):
        return {
            'io_id': self.io_id,
            'short_desc': self.short_desc,
            'ias_type': self.ias_type
        }
