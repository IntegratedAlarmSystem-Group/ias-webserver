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

    class Meta:
        db_table = 'IASIO'
