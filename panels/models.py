import os
from django.db import models
from ias_webserver.settings import FILES_LOCATION


PERMISSIONS = ('add', 'change', 'delete', 'view')
""" Models Permissions """


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


class PlacemarkType(models.Model):
    """ Type of placemark """

    name = models.CharField(max_length=64, unique=True)
    """ Name of the type """


class PlacemarkGroup(models.Model):
    """ Groups of position marks, used to refer to layers of related position
    marks that interact with each other """

    name = models.CharField(
        max_length=64, null=False, unique=True)
    """ Name of the group """

    description = models.CharField(max_length=256, null=True, blank=True)
    """ Brief description of the group """


class Placemark(models.Model):
    """ Elements to be displayed in the graphical components
    (maps, floor plans, etc.) """

    name = models.CharField(
        max_length=64, null=False, unique=True)
    """ ID of the placemark """

    description = models.CharField(max_length=256, null=True, blank=True)
    """ Brief description of the placemark """

    type = models.ForeignKey(
        PlacemarkType, on_delete=models.CASCADE, related_name='placemarks'
    )
    """ Type of the placemark """

    group = models.ForeignKey(
        PlacemarkGroup, on_delete=models.SET_NULL, related_name='placemarks',
        null=True, blank=True
    )

    class Meta:
        default_permissions = PERMISSIONS
    """ Additional options for the model """

    @staticmethod
    def has_read_permission(request):
        return request.user.has_perm('panels.view_placemark')


class View(models.Model):
    """ Available Views """

    name = models.CharField(max_length=15, null=False, unique=True)
    """ Name of the View """

    def __str__(self):
        """ Return a string representation of the view """
        return str(self.name)


class Type(models.Model):
    """ Available Alarms Types """

    name = models.CharField(max_length=15, null=False, unique=True)
    """ Name of the Type """

    def __str__(self):
        """ Return a string representation of the type """
        return str(self.name)


class AlarmConfig(models.Model):
    """ Relation between alarms and view elements """

    alarm_id = models.CharField(max_length=64, null=False, unique=True)
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

    placemark = models.OneToOneField(
        Placemark, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alarm')
    """ Id of the position in the maps """

    tags = models.CharField(max_length=64, null=True, blank=True)
    """ Other custom data """

    class Meta:
        unique_together = ("alarm_id", "view")
        default_permissions = PERMISSIONS
    """ Meta class of the AlarmConfig """

    def __str__(self):
        """ Return a string representation of the AlarmConfig """
        return str(self.view.name) + ": " + str(self.alarm_id)

    @staticmethod
    def has_read_permission(request):
        return request.user.has_perm('panels.view_alarmconfig')
