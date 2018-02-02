from django.db import models

# Create your models here.


class Iasio(models.Model):
    io_id = models.CharField(
        max_length=64, null=False, primary_key=True, db_column='io_id'
    )
    short_desc = models.TextField(db_column='shortDesc', max_length=256)
    refresh_rate = models.IntegerField(null=False, db_column='refreshRate')
    ias_type = models.CharField(max_length=16, null=False, db_column='iasType')

    def save(self, *args, **kwargs):
        self.ias_type = self.ias_type.upper()
        super(Iasio, self).save(*args, **kwargs)

    @classmethod
    def get_refresh_rate(self, core_id):
        """ Return the refresh rate specified for an iasio or a default value
        if the iasio is not created in the database """
        try:
            return Iasio.objects.get(io_id=core_id).refresh_rate
        except:
            return 2000

    class Meta:
        db_table = 'IASIO'
