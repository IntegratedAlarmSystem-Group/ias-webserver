import os
import json
import mock
from django.test import TestCase
from panels.models import AlarmConfig
from panels.models import (
    File,
    PlacemarkType,
    PlacemarkGroup,
    Placemark
)

MOCK_FILES_PATH = os.path.join(os.getcwd(), 'panels', 'tests')


class AlarmConfigFormatTestCase(TestCase):
    """ This class defines the test suite for the AlarmConfig class tests"""

    def setUp(self):
        self.expected_configurations = []
        for alarm_id in [
            "alarm_id_1", "alarm_id_1_children", "alarm_id_2", "alarm_id_3"
        ]:
            conf = AlarmConfig({})
            conf.alarm_id = alarm_id
            conf.custom_name = "{}_custom_name".format(alarm_id)
            if alarm_id in ["alarm_id_2", "alarm_id_3"]:
                conf.custom_name = ""
            conf.type = "{}_type".format(alarm_id)
            conf.view = "{}_view".format(alarm_id)
            conf.placemark = "{}_placemark".format(alarm_id)
            conf.group = "{}_group".format(alarm_id)
            conf.children = []
            if alarm_id in ["alarm_id_1"]:
                conf.children = ["{}_children".format(alarm_id)]
            self.expected_configurations.append(conf)

    @mock.patch('panels.models.FileManager.all_config_files')
    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    def tests_get_configurations_from_file_with_a_list_format(
        self,
        mock_location,
        mock_all_config_files
    ):
        mock_location.return_value = MOCK_FILES_PATH
        mock_all_config_files.return_value = [
            File('mock_list_config', 'mock_list_config.json')]
        sorted_configurations = sorted(
            AlarmConfig.objects.all(), key=lambda x: x.alarm_id)
        sorted_expected = sorted(
            self.expected_configurations, key=lambda x: x.alarm_id)
        self.assertEqual(
            sorted_configurations, sorted_expected, 'Not equal configurations')

    @mock.patch('panels.models.FileManager.all_config_files')
    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    def tests_get_configurations_from_file_with_a_dictionary_format(
        self,
        mock_location,
        mock_all_config_files
    ):
        mock_location.return_value = MOCK_FILES_PATH
        mock_all_config_files.return_value = [
            File('mock_dict_config', 'mock_dict_config.json')]
        sorted_configurations = sorted(
            AlarmConfig.objects.all(), key=lambda x: x.alarm_id)
        sorted_expected = sorted(
            self.expected_configurations, key=lambda x: x.alarm_id)
        self.assertEqual(
            sorted_configurations, sorted_expected, 'Not equal configurations')


class PlacemarkTypeModelsTestCase(TestCase):
    """ This class defines the test suite for the Placemark Type model tests"""

    def setUp(self):
        self.type_name = "pads"
        self.new_type_name = "room"
        self.old_count = PlacemarkType.objects.count()

    def test_create_type(self):
        """ Test if we can create a type"""
        # Act:
        PlacemarkType.objects.create(
            name=self.type_name
        )
        # Asserts:
        self.new_count = PlacemarkType.objects.count()
        self.assertEqual(
            self.old_count + 1, self.new_count,
            'The PlacemarkType was not created in the database'
        )

    def test_retrieve_type(self):
        """ Test if we can retrieve a type"""
        # Arrage:
        type = PlacemarkType.objects.create(
            name=self.type_name
        )
        # Act:
        retrieved_type = PlacemarkType.objects.get(pk=type.pk)
        # Asserts:
        self.assertEqual(
            retrieved_type.name, self.type_name,
            'PlacemarkType was not retrieved'
        )

    def test_update_type(self):
        """ Test if we can update a type"""
        # Arrage:
        type = PlacemarkType.objects.create(
            name=self.type_name
        )
        self.old_count = PlacemarkType.objects.count()
        # Act:
        type.name = self.new_type_name
        type.save()
        # Asserts:
        self.new_count = PlacemarkType.objects.count()
        self.assertEqual(
            self.old_count, self.new_count,
            'A new PlacemarkType was created in the database'
        )
        retrieved_type = PlacemarkType.objects.get(pk=type.pk)
        self.assertEqual(
            retrieved_type.name, self.new_type_name,
            'PlacemarkType was not updated with the given name'
        )

    def test_delete_type(self):
        """ Test if we can delete a type"""
        # Arrage:
        type = PlacemarkType.objects.create(
            name=self.type_name
        )
        self.old_count = PlacemarkType.objects.count()
        # Act:
        type.delete()
        # Asserts:
        self.new_count = PlacemarkType.objects.count()
        self.assertEqual(
            self.old_count - 1, self.new_count,
            'The PlacemarkType was not deleted in the database'
        )


class PlacemarkGroupModelsTestCase(TestCase):
    """This class defines the test suite for the Placemark Group model tests"""

    def setUp(self):
        self.group_name = "INNER"
        self.new_group_name = "ACA"
        self.old_count = PlacemarkGroup.objects.count()

    def test_create_group(self):
        """ Test if we can create a type"""
        # Act:
        PlacemarkGroup.objects.create(
            name=self.group_name,
            description="brief description"
        )
        # Asserts:
        self.new_count = PlacemarkGroup.objects.count()
        self.assertEqual(
            self.old_count + 1, self.new_count,
            'The PlacemarkGroup was not created in the database'
        )

    def test_retrieve_group(self):
        """ Test if we can retrieve a type"""
        # Arrage:
        type = PlacemarkGroup.objects.create(
            name=self.group_name
        )
        # Act:
        retrieved_group = PlacemarkGroup.objects.get(pk=type.pk)
        # Asserts:
        self.assertEqual(
            retrieved_group.name, self.group_name,
            'PlacemarkGroup was not retrieved'
        )

    def test_update_group(self):
        """ Test if we can update a type"""
        # Arrage:
        type = PlacemarkGroup.objects.create(
            name=self.group_name
        )
        self.old_count = PlacemarkGroup.objects.count()
        # Act:
        type.name = self.new_group_name
        type.save()
        # Asserts:
        self.new_count = PlacemarkGroup.objects.count()
        self.assertEqual(
            self.old_count, self.new_count,
            'A new PlacemarkGroup was created in the database'
        )
        retrieved_group = PlacemarkGroup.objects.get(pk=type.pk)
        self.assertEqual(
            retrieved_group.name, self.new_group_name,
            'PlacemarkGroup was not updated with the given name'
        )

    def test_delete_group(self):
        """ Test if we can delete a type"""
        # Arrage:
        type = PlacemarkGroup.objects.create(
            name=self.group_name
        )
        self.old_count = PlacemarkGroup.objects.count()
        # Act:
        type.delete()
        # Asserts:
        self.new_count = PlacemarkGroup.objects.count()
        self.assertEqual(
            self.old_count - 1, self.new_count,
            'The PlacemarkGroup was not deleted in the database'
        )


class PlacemarkTestCase(TestCase):
    """ This class defines the test suite for the Placemark model tests """

    def setUp(self):
        self.name = "placemark_1"
        self.type = PlacemarkType.objects.create(
            name="pad"
        )
        self.new_type = PlacemarkType.objects.create(
            name="fire_sensor"
        )
        self.group = PlacemarkGroup.objects.create(
            name="fire_sensor"
        )
        self.old_count = Placemark.objects.count()

    def test_create_placemark(self):
        """ Test if we can create a placemark"""
        # Act:
        Placemark.objects.create(
            name=self.name,
            type=self.type
        )
        # Asserts:
        self.new_count = Placemark.objects.count()
        self.assertEqual(
            self.old_count + 1, self.new_count,
            'The Placemark was not created in the database'
        )

    def test_create_placemark_with_group(self):
        """ Test if we can create a placemark with a group"""
        # Act:
        Placemark.objects.create(
            name=self.name,
            type=self.type,
            group=self.group
        )
        # Asserts:
        self.new_count = Placemark.objects.count()
        self.assertEqual(
            self.old_count + 1, self.new_count,
            'The Placemark was not created in the database'
        )

    def test_retrieve_placemark(self):
        """ Test if we can retrieve a placemark"""
        # Arrage:
        placemark = Placemark.objects.create(
            name=self.name,
            type=self.type
        )
        # Act:
        retrieved_placemark = Placemark.objects.get(pk=placemark.pk)
        # Asserts:
        self.assertEqual(
            retrieved_placemark.name, self.name,
            'Placemark was not retrieved'
        )

    def test_update_placemark(self):
        """ Test if we can update a placemark"""
        # Arrage:
        placemark = Placemark.objects.create(
            name=self.name,
            type=self.type
        )
        self.old_count = Placemark.objects.count()
        # Act:
        placemark.type = self.new_type
        placemark.save()
        # Asserts:
        self.new_count = Placemark.objects.count()
        self.assertEqual(
            self.old_count, self.new_count,
            'A new Placemark was created in the database'
        )
        retrieved_placemark = Placemark.objects.get(pk=placemark.pk)
        self.assertEqual(
            retrieved_placemark.type, self.new_type,
            'Placemark was not updated with the given name'
        )

    def test_delete_placemark(self):
        """ Test if we can delete a placemark"""
        # Arrage:
        placemark = Placemark.objects.create(
            name=self.name,
            type=self.type
        )
        self.old_count = Placemark.objects.count()
        # Act:
        placemark.delete()
        # Asserts:
        self.new_count = Placemark.objects.count()
        self.assertEqual(
            self.old_count - 1, self.new_count,
            'The Placemark was not deleted in the database'
        )
