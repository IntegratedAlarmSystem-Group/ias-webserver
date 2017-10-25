from django.db import models

# Create your models here.
class Alarm(models.Model):
    value = models.IntegerField(default=0, blank=False, null=False)
    mode = models.PositiveIntegerField(default=0, blank=False, null=False)
    core_timestamp = models.PositiveIntegerField(blank=False, null=False)
    core_id = models.CharField(max_length=100)
    running_id = models.CharField(max_length=100)

    def __str__(self):
        """returns a string representation of the object"""
        return str(self.core_id) + '=' + str(self.value)
