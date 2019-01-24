import os
import glob
import json
from django.db import models
from ias_webserver.settings import FILES_LOCATION


PERMISSIONS = ('add', 'change', 'delete', 'view')
""" Models Permissions """


class FileManager:

    def _get_files_absolute_location(self):
        """ Return the path for the folder with the configuration files
        """
        return os.path.join(os.getcwd(), FILES_LOCATION)

    def basenames(self):
        """ Return a list with the basename of the files
            without the .json extension
        """
        abs_path = self._get_files_absolute_location()
        return [os.path.splitext(f)[0] for f in glob.glob1(abs_path, '*.json')]

    def all(self):
        """ Return a list with instances for each available file
        """
        basenames = self.basenames()
        return [
            File(key=name, url='{}.json'.format(name)) for name in basenames
        ]

    def all_config_files(self):
        """ Return a list with instances for configuration files
        """
        return [
            file for file in self.all() if file.is_config_file()
        ]

    def get_instance_for_localfile(self, file_basename):
        """ Return an instance for a file, according to a requested basename,
            only if the file exists in the folder
        """
        key = file_basename
        available_files = self.basenames()
        if key in available_files:
            return File(key=key, url='{}.json'.format(key))


class File:
    """
    Class to manage the information about local files
    with the configuration of the alarms display
    """

    objects = FileManager()

    def __init__(self, key, url):
        self.key = key
        """ Key to identify the File on the client side """

        self.url = url
        """ URL with the location of the File """

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

    def get_content_data(self):
        """ Returns a Python object with data from the json content of the file
        """
        if self.key in self.objects.basenames():
            url = self.get_full_url()
            with open(url) as f:
                data = json.load(f)
            return data

    def _collect_configurations_from_list(self, configurations, full_list):
        if isinstance(configurations, list):
            for config in configurations:
                full_list += [AlarmConfig(config)]
                if len(config['children']) > 0:
                    self._collect_configurations_from_list(
                        config['children'], full_list)

    def _collect_configurations_from_dict(self, data, full_list):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    self._collect_configurations_from_dict(value, full_list)
                else:
                    if isinstance(value, list):
                        self._collect_configurations_from_list(
                            value, full_list)

    def get_configurations(self, update_placemark_values={}):
        """ Returns a list of instances for all the configurations
            recognized in the file
        """
        if self.is_config_file():
            config_list = []
            data = self.get_configuration_data(update_placemark_values)
            if data is not None:
                if isinstance(data, dict):
                    self._collect_configurations_from_dict(data, config_list)
                if isinstance(data, list):
                    self._collect_configurations_from_list(data, config_list)
            return config_list

    def _traverse_and_update_configurations_from_list(
        self, configurations, update_placemark_values
    ):
        if isinstance(configurations, list):
            for config in configurations:
                placemark_id = config['placemark']
                if placemark_id in update_placemark_values:
                    config['placemark'] = update_placemark_values[
                        placemark_id
                    ]
                if len(config['children']) > 0:
                    self._traverse_and_update_configurations_from_list(
                        config['children'], update_placemark_values)

    def _locate_and_update_configurations_from_dict(
        self, data, update_placemark_values
    ):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    self._locate_and_update_configurations_from_dict(
                        value, update_placemark_values)
                else:
                    if isinstance(value, list):
                        self._traverse_and_update_configurations_from_list(
                            value, update_placemark_values)

    def get_configuration_data(self, update_placemark_values={}):
        """ Returns a Python object with data from the json content of the file
            and required updates for the configuration
        """
        if self.is_config_file():
            if len(update_placemark_values) == 0:
                return self.get_content_data()
            else:
                data = self.get_content_data()
                if data is not None:
                    if isinstance(data, dict):
                        self._locate_and_update_configurations_from_dict(
                            data, update_placemark_values)
                    if isinstance(data, list):
                        self._traverse_and_update_configurations_from_list(
                            data, update_placemark_values)
                return data

    def is_config_file(self):
        return '_config' in self.key

    @classmethod
    def _get_absolute_location(self):
        return self.objects._get_files_absolute_location()


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

    @staticmethod
    def has_create_permission(request):
        return False


class AlarmConfigManager:

    def all(self):
        full_config_list = []
        for file in File.objects.all_config_files():
            full_config_list += file.get_configurations()
        return full_config_list

    def get_file_configurations(self, key, update_placemark_values={}):
        file = File.objects.get_instance_for_localfile(key)
        if file is not None:
            if file.is_config_file():
                full_config_list = file.get_configurations(
                    update_placemark_values=update_placemark_values
                )
                return full_config_list

    def get_file_configuration_data(self, key, update_placemark_values={}):
        file = File.objects.get_instance_for_localfile(key)
        if file is not None:
            if file.is_config_file():
                full_config_list = file.get_configuration_data(
                    update_placemark_values=update_placemark_values
                )
                return full_config_list


class AlarmConfig:

    objects = AlarmConfigManager()

    def __init__(self, config):
        self.alarm_id = config.get('alarm_id', '')
        self.custom_name = config.get('custom_name', '')
        self.type = config.get('type', '')
        self.view = config.get('view', '')
        self.placemark = config.get('placemark', '')
        self.group = config.get('group', '')
        self.children = [
            c['alarm_id'] for c in config.get('children', [])
        ]

    def __str__(self):
        """ Return a string representation for the file """
        return '{} : {}'.format(self.alarm_id, self.custom_name)

    def to_dict(self):
        return {
            'alarm_id': self.alarm_id,
            'custom_name': self.custom_name,
            'type': self.type,
            'view': self.view,
            'placemark': self.placemark,
            'group': self.group,
            'children': self.children
        }
