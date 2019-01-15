import os
import glob
from django.db import models
from ias_webserver.settings import FILES_LOCATION


PERMISSIONS = ('add', 'change', 'delete', 'view')
""" Models Permissions """


class LocalFileManager:

    def _get_files_absolute_location(self):
        """ Return the path for the folder with the configuration files
        """
        return os.path.join(os.getcwd(), FILES_LOCATION)

    def get_files_list(self):
        """ Return a list with the basename of the files
            without the .json extension
        """
        abs_path = self._get_files_absolute_location()
        return [os.path.splitext(f)[0] for f in glob.glob1(abs_path, '*.json')]

    def get_instances_list(self):
        """ Return a list with instances for each available file
        """
        basenames = self.get_files_list()
        return [
            self.get_instance_for_localfile(name) for name in basenames
        ]

    def get_instance_for_localfile(self, file_basename):
        """ Return an instance for a file, according to a requested basename,
            only if the file exists in the folder
        """
        key = file_basename
        available_files = self.get_files_list()
        if key in available_files:
            return LocalFile(key=key, url='{}.json'.format(key))


class LocalFile:
    """
    Class to manage the information about local files
    with the alarms' configuration
    """

    objects = LocalFileManager()

    def __init__(self, key, url):
        self.key = key
        self.url = url

    def __str__(self):
        """ Return a string representation for the file """
        return '{} : {}'.format(self.key, self.url)

    def to_dict(self):
        """ Return the file as a dictionary """
        return {
            "key": self.key,
            "url": self.url
        }

    def get_full_url(self):
        """ Return the full url of the file """
        return os.path.join(self._get_absolute_location(), self.url)

    @classmethod
    def _get_absolute_location(self):
        return self.objects._get_files_absolute_location()

    @staticmethod
    def has_read_permission(request):
        return request.user.has_perm('panels.view_file')


class File(models.Model):
    """ General purpose file """

    key = models.CharField(max_length=30, unique=True)
    """ Key to identify the File on the client side """

    url = models.CharField(max_length=256)
    """ URL with the location of the File """

    class Meta:
        default_permissions = PERMISSIONS
    """ Additional options for the model """

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

    @staticmethod
    def has_create_permission(request):
        return request.user.has_perm('panels.add_file')

    @staticmethod
    def has_read_permission(request):
        return request.user.has_perm('panels.view_file')

    def has_object_read_permission(self, request):
        return request.user.has_perm('panels.view_file')

    @staticmethod
    def has_update_permission(request):
        return request.user.has_perm('panels.change_file')

    def has_object_update_permission(self, request):
        return request.user.has_perm('panels.change_file')

    @staticmethod
    def has_destroy_permission(request):
        return request.user.has_perm('panels.delete_file')

    def has_object_destroy_permission(self, request):
        return request.user.has_perm('panels.delete_file')


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

    name = models.CharField(max_length=30, null=False, unique=True)
    """ Name of the View """

    def __str__(self):
        """ Return a string representation of the view """
        return str(self.name)


class Type(models.Model):
    """ Available Alarms Types """

    name = models.CharField(max_length=30, null=False, unique=True)
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

    custom_name = models.CharField(max_length=30, null=True, blank=True)
    """ Custom name to show in the display """

    placemark = models.OneToOneField(
        Placemark, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alarm')
    """ Id of the position in the maps """

    tags = models.CharField(max_length=64, null=True, blank=True)
    """ Other custom data """

    @staticmethod
    def has_write_permission(request):
        return False

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
