from django.test import TestCase
from panels.models import (
    File,
    View,
    Type,
    AlarmConfig,
    PlacemarkType,
    PlacemarkGroup,
    Placemark,
    CoordinateType
)


class FileModelsTestCase(TestCase):
    """This class defines the test suite for the File model tests"""

    def setUp(self):
        self.url = 'dummy.url.com'
        self.key = 'dummy_key'
        self.new_url = 'new_dummy.url.com'
        self.old_count = File.objects.count()

    def test_create_file(self):
        """ Test if we can create a file"""
        # Act:
        File.objects.create(
            key=self.key,
            url=self.url
        )
        # Asserts:
        self.new_count = File.objects.count()
        self.assertEqual(
            self.old_count + 1, self.new_count,
            'The File was not created in the database'
        )

    def test_retrieve_file(self):
        """ Test if we can retrieve a file"""
        # Arrage:
        file = File.objects.create(
            key=self.key,
            url=self.url
        )
        # Act:
        retrieved_file = File.objects.get(pk=file.pk)
        # Asserts:
        self.assertEqual(
            retrieved_file.url, self.url,
            'File was not retrieved'
        )

    def test_update_file(self):
        """ Test if we can update a file"""
        # Arrage:
        file = File.objects.create(
            key=self.key,
            url=self.url
        )
        self.old_count = File.objects.count()
        # Act:
        file.url = self.new_url
        file.save()
        # Asserts:
        self.new_count = File.objects.count()
        self.assertEqual(
            self.old_count, self.new_count,
            'A new File was created in the database'
        )
        retrieved_file = File.objects.get(pk=file.pk)
        self.assertEqual(
            retrieved_file.url, self.new_url,
            'File was not created with the given URL'
        )

    def test_delete_file(self):
        """ Test if we can delete a file"""
        # Arrage:
        file = File.objects.create(
            key=self.key,
            url=self.url
        )
        self.old_count = File.objects.count()
        # Act:
        file.delete()
        # Asserts:
        self.new_count = File.objects.count()
        self.assertEqual(
            self.old_count - 1, self.new_count,
            'The File was not deleted in the database'
        )


class ViewModelsTestCase(TestCase):
    """ This class defines the test suite for the View model tests """

    def setUp(self):
        self.view_name = "antennas"
        self.new_view_name = "weather"
        self.old_count = View.objects.count()

    def test_create_view(self):
        """ Test if we can create a view"""
        # Act:
        View.objects.create(
            name=self.view_name
        )
        # Asserts:
        self.new_count = View.objects.count()
        self.assertEqual(
            self.old_count + 1, self.new_count,
            'The View was not created in the database'
        )

    def test_retrieve_view(self):
        """ Test if we can retrieve a view"""
        # Arrage:
        view = View.objects.create(
            name=self.view_name
        )
        # Act:
        retrieved_view = View.objects.get(pk=view.pk)
        # Asserts:
        self.assertEqual(
            retrieved_view.name, self.view_name,
            'View was not retrieved'
        )

    def test_update_view(self):
        """ Test if we can update a view"""
        # Arrage:
        view = View.objects.create(
            name=self.view_name
        )
        self.old_count = View.objects.count()
        # Act:
        view.name = self.new_view_name
        view.save()
        # Asserts:
        self.new_count = View.objects.count()
        self.assertEqual(
            self.old_count, self.new_count,
            'A new View was created in the database'
        )
        retrieved_view = View.objects.get(pk=view.pk)
        self.assertEqual(
            retrieved_view.name, self.new_view_name,
            'View was not updated with the given name'
        )

    def test_delete_view(self):
        """ Test if we can delete a view"""
        # Arrage:
        view = View.objects.create(
            name=self.view_name
        )
        self.old_count = View.objects.count()
        # Act:
        view.delete()
        # Asserts:
        self.new_count = View.objects.count()
        self.assertEqual(
            self.old_count - 1, self.new_count,
            'The View was not deleted in the database'
        )


class TypeModelsTestCase(TestCase):
    """ This class defines the test suite for the Type model tests """

    def setUp(self):
        self.type_name = "temperature"
        self.new_type_name = "humidity"
        self.old_count = Type.objects.count()

    def test_create_type(self):
        """ Test if we can create a type"""
        # Act:
        Type.objects.create(
            name=self.type_name
        )
        # Asserts:
        self.new_count = Type.objects.count()
        self.assertEqual(
            self.old_count + 1, self.new_count,
            'The Type was not created in the database'
        )

    def test_retrieve_type(self):
        """ Test if we can retrieve a type"""
        # Arrage:
        type = Type.objects.create(
            name=self.type_name
        )
        # Act:
        retrieved_type = Type.objects.get(pk=type.pk)
        # Asserts:
        self.assertEqual(
            retrieved_type.name, self.type_name,
            'Type was not retrieved'
        )

    def test_update_type(self):
        """ Test if we can update a type"""
        # Arrage:
        type = Type.objects.create(
            name=self.type_name
        )
        self.old_count = Type.objects.count()
        # Act:
        type.name = self.new_type_name
        type.save()
        # Asserts:
        self.new_count = Type.objects.count()
        self.assertEqual(
            self.old_count, self.new_count,
            'A new Type was created in the database'
        )
        retrieved_type = Type.objects.get(pk=type.pk)
        self.assertEqual(
            retrieved_type.name, self.new_type_name,
            'Type was not updated with the given name'
        )

    def test_delete_type(self):
        """ Test if we can delete a type"""
        # Arrage:
        type = Type.objects.create(
            name=self.type_name
        )
        self.old_count = Type.objects.count()
        # Act:
        type.delete()
        # Asserts:
        self.new_count = Type.objects.count()
        self.assertEqual(
            self.old_count - 1, self.new_count,
            'The Type was not deleted in the database'
        )


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
            x=12.3,
            y=12.1,
            coordinates_type=CoordinateType.GEOGRAPHICAL,
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
            x=12.3,
            y=12.1,
            coordinates_type=CoordinateType.CARTESIAN,
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
            x=12.3,
            y=12.1,
            coordinates_type=CoordinateType.GEOGRAPHICAL,
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
            x=12.3,
            y=12.1,
            coordinates_type=CoordinateType.GEOGRAPHICAL,
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
            x=12.3,
            y=12.1,
            coordinates_type=CoordinateType.GEOGRAPHICAL,
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


class AlarmConfigModelsTestCase(TestCase):
    """ This class defines the test suite for the AlarmConfig model tests """

    def setUp(self):
        self.alarm_id = "dummy_alarm"
        self.view = View.objects.create(
            name="weather"
        )
        self.type = Type.objects.create(
            name="temperature"
        )
        self.new_type = Type.objects.create(
            name="humidity"
        )
        self.old_count = AlarmConfig.objects.count()

    def test_create_alarm_config(self):
        """ Test if we can create a alarm_config"""
        # Act:
        AlarmConfig.objects.create(
            alarm_id=self.alarm_id,
            view=self.view,
            type=self.type
        )
        # Asserts:
        self.new_count = AlarmConfig.objects.count()
        self.assertEqual(
            self.old_count + 1, self.new_count,
            'The AlarmConfig was not created in the database'
        )

    def test_retrieve_alarm_config(self):
        """ Test if we can retrieve a alarm_config"""
        # Arrage:
        alarm_config = AlarmConfig.objects.create(
            alarm_id=self.alarm_id,
            view=self.view,
            type=self.type
        )
        # Act:
        retrieved_alarm_config = AlarmConfig.objects.get(pk=alarm_config.pk)
        # Asserts:
        self.assertEqual(
            retrieved_alarm_config.alarm_id, self.alarm_id,
            'AlarmConfig was not retrieved'
        )

    def test_update_alarm_config(self):
        """ Test if we can update a alarm_config"""
        # Arrage:
        alarm_config = AlarmConfig.objects.create(
            alarm_id=self.alarm_id,
            view=self.view,
            type=self.type
        )
        self.old_count = AlarmConfig.objects.count()
        # Act:
        alarm_config.type = self.new_type
        alarm_config.save()
        # Asserts:
        self.new_count = AlarmConfig.objects.count()
        self.assertEqual(
            self.old_count, self.new_count,
            'A new AlarmConfig was created in the database'
        )
        retrieved_alarm_config = AlarmConfig.objects.get(pk=alarm_config.pk)
        self.assertEqual(
            retrieved_alarm_config.type, self.new_type,
            'AlarmConfig was not updated with the given name'
        )

    def test_delete_alarm_config(self):
        """ Test if we can delete a alarm_config"""
        # Arrage:
        alarm_config = AlarmConfig.objects.create(
            alarm_id=self.alarm_id,
            view=self.view,
            type=self.type
        )
        self.old_count = AlarmConfig.objects.count()
        # Act:
        alarm_config.delete()
        # Asserts:
        self.new_count = AlarmConfig.objects.count()
        self.assertEqual(
            self.old_count - 1, self.new_count,
            'The AlarmConfig was not deleted in the database'
        )

    def test_create_alarm_config_with_parent(self):
        # Arrange:
        alarm_config_parent = AlarmConfig.objects.create(
            alarm_id="parent_alarm",
            view=self.view,
            type=self.type
        )
        # Act:
        self.old_count = AlarmConfig.objects.count()
        alarm_config = AlarmConfig.objects.create(
            alarm_id="child_alarm",
            view=self.view,
            type=self.type,
            parent=alarm_config_parent
        )
        # Asserts:
        self.new_count = AlarmConfig.objects.count()
        self.assertEqual(
            self.old_count + 1, self.new_count,
            'The AlarmConfig with a parent was not created in the database'
        )
        retrieved_alarm_config = AlarmConfig.objects.get(pk=alarm_config.pk)
        self.assertEqual(
            retrieved_alarm_config.parent, alarm_config_parent,
            'AlarmConfig has not a reference to its parent'
        )
        retrieved_alarm_config_parent = AlarmConfig.objects.get(
            pk=alarm_config_parent.pk
        )
        self.assertEqual(
            retrieved_alarm_config_parent.nested_alarms.count(), 1,
            'AlarmConfigParent has not a reference to its nested alarms'
        )

    def test_create_alarm_config_with_placemark(self):
        # Arrange:
        placemark_type = PlacemarkType.objects.create(
            name="pad"
        )
        placemark = Placemark.objects.create(
            name="placemark",
            x=0.0,
            y=0.0,
            coordinates_type=CoordinateType.GEOGRAPHICAL,
            type=placemark_type
        )
        # Act:
        self.old_count = AlarmConfig.objects.count()
        alarm_config = AlarmConfig.objects.create(
            alarm_id=self.alarm_id,
            view=self.view,
            type=self.type,
            placemark=placemark
        )
        # Asserts:
        self.new_count = AlarmConfig.objects.count()
        self.assertEqual(
            self.old_count + 1, self.new_count,
            'The AlarmConfig with a placemark was not created in the database'
        )
        retrieved_alarm_config = AlarmConfig.objects.get(pk=alarm_config.pk)
        self.assertEqual(
            retrieved_alarm_config.placemark, placemark,
            'AlarmConfig has not a reference to the placemark'
        )
        retrieved_placemark = Placemark.objects.get(
            pk=placemark.pk
        )
        self.assertEqual(
            retrieved_placemark.alarm, alarm_config,
            'Placemark has not a reference to it related alarm'
        )
