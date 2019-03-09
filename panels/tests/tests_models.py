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


class AlarmConfigTestBase:

    def get_files_from_keys(self, file_keys):
        return [
            File(key, "{}.json".format(key)) for key in file_keys
        ]

    def get_mock_all_files(self):
        return self.get_files_from_keys(["mock_dict_config", "mock_config"])

    def get_mock_list_config_files(self):
        return self.get_files_from_keys(["mock_list_config"])

    def get_mock_dict_config_files(self):
        return self.get_files_from_keys(["mock_dict_config"])

    def get_mock_config_files(self):
        return self.get_files_from_keys(["mock_config"])

    def get_base_expected_configurations(self):
        """ Expected configurations
            for the mock_list_config.json and mock_dict_config.json files
        """
        expected_configurations = []
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
            expected_configurations.append(conf)
        return expected_configurations

    def get_additional_expected_configurations(self):
        """ Additional configurations for the mock_config.json file """
        expected_configurations = []
        expected_children_ids = {
            'a': ['a1', 'a2'],
            'a1': [],
            'a2': [],
            'b': [],
            'c': [],
            'd': ['e'],
            'e': ['f'],
            'f': ['g'],
            'g': []
        }
        for key in expected_children_ids:
            conf = AlarmConfig({})
            conf.alarm_id = key
            conf.custom_name = '{}_custom_name'.format(key)
            conf.type = '{}_type'.format(key)
            conf.view = '{}_view'.format(key)
            conf.placemark = '{}_placemark'.format(key)
            conf.group = '{}_group'.format(key)
            conf.children = expected_children_ids[key]
            expected_configurations.append(conf)
        return expected_configurations


class AlarmConfigFormatTestCase(TestCase, AlarmConfigTestBase):
    """ This class defines the test suite for the AlarmConfig class tests
        to get a list with all the configurations from a file
        with content in json format
    """

    def setUp(self):
        self.expected_configurations = self.get_base_expected_configurations()

    @mock.patch('panels.models.FileManager.all_config_files')
    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    def tests_get_configurations_from_config_files_with_a_list_format(
        self,
        mock_location,
        mock_all_config_files
    ):
        # Arrange:
        mock_location.return_value = MOCK_FILES_PATH
        mock_all_config_files.return_value = self.get_mock_list_config_files()
        # Act:
        confs = AlarmConfig.objects.all()
        # Assert:
        sorted_configurations = sorted(confs, key=lambda x: x.alarm_id)
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
        # Arrange:
        mock_location.return_value = MOCK_FILES_PATH
        mock_all_config_files.return_value = self.get_mock_dict_config_files()
        # Act:
        confs = AlarmConfig.objects.all()
        # Assert:
        sorted_configurations = sorted(confs, key=lambda x: x.alarm_id)
        sorted_expected = sorted(
            self.expected_configurations, key=lambda x: x.alarm_id)
        self.assertEqual(
            sorted_configurations, sorted_expected, 'Not equal configurations')


class AlarmConfigAllTestCase(TestCase, AlarmConfigTestBase):
    """ This class defines the test suite for the AlarmConfig class tests
        to get a list with all the configurations from the configuration files
    """

    def setUp(self):
        self.config_files = self.get_mock_all_files()
        expected = self.get_base_expected_configurations()
        expected += self.get_additional_expected_configurations()
        self.expected_configurations = expected

    @mock.patch('panels.models.FileManager.all_config_files')
    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    def tests_get_configurations_from_config_files(
        self,
        mock_location,
        mock_all_config_files
    ):
        # Arrange:
        mock_location.return_value = MOCK_FILES_PATH
        mock_all_config_files.return_value = self.config_files
        # Act:
        confs = AlarmConfig.objects.all()
        # Assert:
        sorted_configurations = sorted(confs, key=lambda x: x.alarm_id)
        sorted_expected = sorted(
            self.expected_configurations, key=lambda x: x.alarm_id)
        self.assertEqual(
            sorted_configurations, sorted_expected, 'Not equal configurations')


class AlarmConfigGetDataFromFileTestCase(TestCase, AlarmConfigTestBase):
    """ This class defines the test suite for the AlarmConfig class tests
        to obtain configuration data from a configuration file
    """
    def setUp(self):
        self.config_files = self.get_mock_dict_config_files()
        self.assertEqual(len(self.config_files), 1, "Expected just one file")
        self.expected_configurations = self.get_base_expected_configurations()

    @mock.patch('panels.models.FileManager.all_config_files')
    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    def tests_get_configurations_from_file(
        self,
        mock_location,
        mock_all_config_files
    ):
        # Arrange:
        mock_location.return_value = MOCK_FILES_PATH
        mock_all_config_files.return_value = self.config_files
        # Act:
        file_key = self.config_files[0].key
        configs = AlarmConfig.objects.get_file_configurations(file_key)
        # Assert:
        sorted_configurations = sorted(configs, key=lambda x: x.alarm_id)
        sorted_expected = sorted(
            self.expected_configurations, key=lambda x: x.alarm_id)
        self.assertEqual(
            sorted_configurations, sorted_expected, 'Not equal configurations')

    @mock.patch('panels.models.FileManager.all_config_files')
    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    def tests_get_configuration_data_from_file(
        self,
        mock_location,
        mock_all_config_files
    ):
        # Arrange:
        mock_location.return_value = MOCK_FILES_PATH
        mock_all_config_files.return_value = self.config_files
        selected_file = self.config_files[0]
        with open(selected_file.get_full_url()) as f:
            configuration_data = json.load(f)
        self.expected_configuration_data = configuration_data
        # Act:
        file_key = self.config_files[0].key
        config_data = AlarmConfig.objects.get_file_configuration_data(file_key)
        # Arrange:
        self.assertEqual(
            config_data, self.expected_configuration_data, 'Unexpected data')


class AlarmConfigGetUpdatedDataFromFileTestCase(TestCase, AlarmConfigTestBase):
    """ This class defines the test suite for the AlarmConfig class tests
        to obtain modified configuration data from a configuration file
    """
    def setUp(self):
        self.config_files = self.get_mock_config_files()
        self.assertEqual(len(self.config_files), 1, "Expected just one file")
        self.placemark_new_values = {
            "a_placemark": "test_a",
            "a1_placemark": "test_a1",
            "a2_placemark": "test_a2",
            "b_placemark": "test_b",
            "c_placemark": "test_c",
            "d_placemark": "test_d",
            "e_placemark": "test_e",
            "f_placemark": "test_f",
            "g_placemark": "test_g"
        }
        expected = self.get_additional_expected_configurations()
        for conf in expected:
            old_placemark = conf.placemark
            conf.placemark = self.placemark_new_values[old_placemark]
        self.expected_configurations = expected

    @mock.patch('panels.models.FileManager.all_config_files')
    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    def tests_get_configurations_from_file(
        self,
        mock_location,
        mock_all_config_files
    ):
        # Arrange:
        mock_location.return_value = MOCK_FILES_PATH
        mock_all_config_files.return_value = self.config_files
        # Act:
        file_key = self.config_files[0].key
        configs = AlarmConfig.objects.get_file_configurations(
            file_key,
            update_placemark_values=self.placemark_new_values
        )
        # Assert:
        sorted_configurations = sorted(configs, key=lambda x: x.alarm_id)
        sorted_expected = sorted(
            self.expected_configurations, key=lambda x: x.alarm_id)
        self.assertEqual(
            sorted_configurations, sorted_expected, 'Not equal configurations')

    @mock.patch('panels.models.FileManager.all_config_files')
    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    def tests_get_configuration_data_from_file(
        self,
        mock_location,
        mock_all_config_files
    ):
        # Arrange:
        mock_location.return_value = MOCK_FILES_PATH
        mock_all_config_files.return_value = self.config_files
        selected_file = self.config_files[0]
        with open(selected_file.get_full_url()) as f:
            data = json.load(f)
        # first list with configurations
        config_list = data["key1a"]["key2a"]["key3a"]
        for conf in config_list:
            old = conf["placemark"]
            conf["placemark"] = self.placemark_new_values[old]
            if conf["alarm_id"] == "a":
                for conf in conf["children"]:
                    old = conf["placemark"]
                    conf["placemark"] = self.placemark_new_values[old]
        # second list with configurations
        config_list = data["key1b"]
        for conf in config_list:
            old = conf["placemark"]
            conf["placemark"] = self.placemark_new_values[old]
        conf = config_list[1]
        while (len(conf["children"]) > 0):
            conf = conf["children"][0]
            old = conf["placemark"]
            conf["placemark"] = self.placemark_new_values[old]
        self.expected_configuration_data = data
        # Act:
        file_key = self.config_files[0].key
        config_data = AlarmConfig.objects.get_file_configuration_data(
            file_key,
            update_placemark_values=self.placemark_new_values
        )
        # Arrange:
        self.assertEqual(
            config_data, self.expected_configuration_data, 'Unexpected data')


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
