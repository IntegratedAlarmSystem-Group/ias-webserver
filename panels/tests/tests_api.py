from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from ias_webserver.settings import FILES_LOCATION
from panels.models import File
from panels.serializers import FileSerializer


class FileApiTestCase(TestCase):
    """Test suite for the registries api views."""

    def setUp(self):
        # Arrange:
        """Define the test suite setup"""
        self.message = 'Shelved because of reasons'
        self.new_data = {'url': 'my_dummy_url'}
        self.files = [
            File.objects.create(url='my_url_1.com'),
            File.objects.create(url='my_url_2.com')
        ]
        self.old_count = File.objects.count()
        self.client = APIClient()

    # ******* CREATE
    def test_api_can_create_file(self):
        """ Test that the api can create a file """
        # Act:
        url = reverse('file-list')
        self.response = self.client.post(url, self.new_data, format='json')
        # Assert:
        created_file = File.objects.get(
            url=self.new_data['url']
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_201_CREATED,
            'The server did not create the file'
        )
        self.assertEqual(
            self.old_count + 1,
            File.objects.count(),
            'The server did not create a new file in the database'
        )
        retrieved_data = {'url': created_file.url}
        self.assertEqual(
            retrieved_data,
            self.new_data,
            'The created file does not match the data sent in the request'
        )

    # ******* RETRIEVE
    def test_api_can_list_the_files(self):
        """ Test that the api can list the files """
        # Act:
        url = reverse('file-list')
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the list of files'
        )
        expected_data = [FileSerializer(t).data for t in self.files]
        self.assertEqual(
            response.data,
            expected_data,
            'The created file does not match the data sent in the request'
        )

    def test_api_can_retrieve_a_file(self):
        """ Test that the api can retrieve a file """
        # Act:
        url = reverse('file-detail', kwargs={'pk': self.files[0].pk})
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the file'
        )
        expected_data = FileSerializer(self.files[0]).data
        self.assertEqual(
            response.data,
            expected_data,
            'The retrieved file data does not match the file in the database'
        )

    # ******* UPDATE
    def test_api_can_update_a_file(self):
        """ Test that the api can update a file """
        # Act:
        url = reverse('file-detail', kwargs={'pk': self.files[0].pk})
        response = self.client.put(url, self.new_data, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not update the file'
        )
        retrieved_file = File.objects.get(pk=self.files[0].pk)
        self.assertEqual(
            retrieved_file.to_dict(),
            self.new_data,
            'The retrieved file data does not match the file in the database'
        )

    # ******* DELETE
    def test_api_can_delete_a_file(self):
        """ Test that the api can delete a file """
        # Act:
        url = reverse('file-detail', kwargs={'pk': self.files[0].pk})
        response = self.client.delete(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
            'The server did not delete the file'
        )
        self.assertEqual(
            self.old_count - 1,
            File.objects.count(),
            'The server did not delete the file in the database'
        )
