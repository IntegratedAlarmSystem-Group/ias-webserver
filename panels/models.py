import os
from django.db import models
from ias_webserver.settings import FILES_LOCATION


class File(models.Model):
    """ General purpose file """

    key = models.CharField(max_length=30, unique=True)
    """ Key to identify the File on the client side """

    url = models.CharField(max_length=256)
    """ URL with the location of the File """

    def __str__(self):
        """ Return a string representation of the file """
        return str(self.key) + ':' + str(self.url)

    def to_dict(self):
        """ Return the ticket as a dictionary """
        return {
            'key': self.key,
            'url': self.url
        }

    def get_full_url(self):
        """ Return the full url of the file """
        return os.path.join(self._get_absolute_location(), self.url)

    @classmethod
    def _get_absolute_location(self):
        return os.path.join(os.getcwd(), FILES_LOCATION)


class View(models.Model):
    """ Available Views """

    name = models.CharField(max_length=15, null=False)
    """ Name of the View """

    def __str__(self):
        """ Return a string representation of the view """
        return str(self.name)


class Type(models.Model):
    """ Available Alarms Types """

    name = models.CharField(max_length=15, null=False)
    """ Name of the Type """

    def __str__(self):
        """ Return a string representation of the type """
        return str(self.name)


class AlarmConfig(models.Model):
    """ Relation between alarms and view elements """

    alarm_id = models.CharField(max_length=64, null=False)
    """ ID of the ALARM """

    view = models.ForeignKey(
        View, on_delete=models.CASCADE, related_name='alarms'
    )
    """ Related View """

    type = models.ForeignKey(
        Type, on_delete=models.CASCADE, related_name='alarms'
    )
    """ Type of the alarm """

    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='nested_alarms'
    )
    """ Reference to an alarm which is displayed as a parent of this alarm """

    custom_name = models.CharField(max_length=15, null=True, blank=True)
    """ Custom name to show in the display """

    placemark = models.CharField(max_length=15, null=True, blank=True)
    """ Id of the position in the maps """

    tags = models.CharField(max_length=64, null=True, blank=True)
    """ Other custom data """

    class Meta:
        """ Meta class of the AlarmConfig """

        unique_together = ("alarm_id", "view")

    def __str__(self):
        """ Return a string representation of the AlarmConfig """
        return str(self.view.name) + ": " + str(self.alarm_id)