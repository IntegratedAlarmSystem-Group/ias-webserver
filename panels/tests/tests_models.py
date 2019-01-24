from django.test import TestCase
from panels.models import (
    PlacemarkType,
    PlacemarkGroup,
    Placemark
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
