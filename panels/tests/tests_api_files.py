import json
import mock
import os
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from panels.models import File
from panels.serializers import FileSerializer


class APITestBase:

    def create_user(self, **kwargs):
        """ Creates a user with selected permissions """
        permissions = kwargs.get('permissions', [])
        username = kwargs.get('username', 'user')
        pwd = kwargs.get('password', 'pwd')
        email = 'user@user.cl'
        user = User.objects.create_user(username, password=pwd, email=email)
        for permission in permissions:
            user.user_permissions.add(permission)
        return user

    def authenticate_client_using_token(self, client, token):
        """ Authenticates a selected API Client using a related User token """
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)


class FileApiTestCase(APITestBase, TestCase):
    """Test suite for the files api views."""

    def setUp(self):
        # Arrange:
        """Define the test suite setup"""
        self.message = 'Shelved because of reasons'
        self.new_data = {
            'key': 'my_new_key',
            'url': 'my_new_url.json'
        }
        self.files = [
            File.objects.create(
                key='my_file_1',
                url='mock.json'
            ),
            File.objects.create(
                key='my_file_2',
                url='my_url_2.json'
            )
        ]
        self.old_count = File.objects.count()
        self.no_permissions_user = self.create_user(
            username='user', password='123', permissions=[])
        self.authenticated_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_client,
            Token.objects.get(user__username=self.no_permissions_user)
        )
        self.client = self.authenticated_client

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
        retrieved_data = created_file.to_dict()
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

    # ******* RETRIEVE FILE
    @mock.patch('panels.models.File._get_absolute_location')
    def test_api_can_get_json_from_file(self, mock):
        """ Test that the api can get a json from a .json file """
        # Arrange:
        mock_location = os.path.join(os.getcwd(), 'panels', 'tests')
        mock.return_value = mock_location
        # Act:
        url = reverse('file-get-json')
        data = {
            'key': 'my_file_1'
        }
        response = self.client.get(url, data, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the file'
        )
        file_url = self.files[0].get_full_url()
        with open(file_url) as f:
            expected_data = json.load(f)
        self.assertEqual(
            response.data,
            expected_data,
            'The retrieved file data does not match the file in the database'
        )

    def test_api_cannot_get_json_if_the_key_does_not_exist(self):
        """ Test that the api cannot get a json if the key does not exist """
        # Act:
        url = reverse('file-get-json')
        data = {
            'key': 'my_fake_key'
        }
        response = self.client.get(url, data, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'The server did retrieve a file'
        )
