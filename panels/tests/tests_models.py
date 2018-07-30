from django.test import TestCase
from panels.models import File


class FileModelsTestCase(TestCase):
    """This class defines the test suite for the File model tests"""

    def setUp(self):
        self.url = 'dummy.url.com'
        self.new_url = 'new_dummy.url.com'
        self.old_count = File.objects.count()

    def test_create_file(self):
        """ Test if we can create a file"""
        # Act:
        file = File.objects.create(url=self.url)
        # Asserts:
        self.new_count = File.objects.count()
        self.assertEqual(
            self.old_count + 1, self.new_count,
            'The File was not created in the database'
        )

    def test_retrieve_file(self):
        """ Test if we can retrieve a file"""
        # Arrage:
        file = File.objects.create(url=self.url)
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
        file = File.objects.create(url=self.url)
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
        file = File.objects.create(url=self.url)
        self.old_count = File.objects.count()
        # Act:
        file.delete()
        # Asserts:
        self.new_count = File.objects.count()
        self.assertEqual(
            self.old_count - 1, self.new_count,
            'The File was not deleted in the database'
        )
