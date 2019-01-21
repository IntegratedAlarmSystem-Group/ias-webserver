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


class FileTestSetup:
    """Class to manage the common setup for testing."""

    def setTestFilesConfig(self):
        """Define the test suite setup"""
        self.files = [
            File('mock', 'mock.json'),
            File('mock_config', 'mock_config.json')
        ]

    def setCommonUsersAndClients(self):
        """ Add unauthenticated and unauthorized users """
        self.unauthorized_user = self.create_user(
            username='user', password='123', permissions=[])
        self.unauthenticated_client = APIClient()
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.unauthorized_user.username)
        )
        self.authenticated_unauthorized_client = client


class ListFile(
    APITestBase, FileTestSetup, TestCase
):
    """ Test suite to test the list request """

    def setUp(self):
        """ Define the test suite setup """
        self.setTestFilesConfig()
        self.setCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[]  # non required permissions
        )
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('files-list')
        return client.get(url, format='json')

    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    def test_api_can_list_the_files(self, mock):
        """ Test that the api can list the files """
        mock_location = os.path.join(os.getcwd(), 'panels', 'tests')
        mock.return_value = mock_location
        client = self.authenticated_authorized_client
        # Act:
        response = self.target_request_from_client(client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the list of files'
        )
        expected_data = [t.to_dict() for t in self.files]
        sorted_response_data = sorted(response.data, key=lambda x: x['key'])
        sorted_expected_data = sorted(expected_data, key=lambda x: x['key'])
        self.assertEqual(
            sorted_response_data,
            sorted_expected_data,
            'The files list does not match the data sent in the request'
        )

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request should not be allowed for an unauthenticated user"
        )


class GetJsonFromFile(
    APITestBase, FileTestSetup, TestCase
):
    """ Test suite to test if the api can get a json
        from a json file
    """

    def setUp(self):
        """ Define the test suite setup """
        self.setTestFilesConfig()
        self.setCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[]  # non required permissions
        )
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('files-get-json')
        data = {
            'key': 'mock'
        }
        return client.get(url, data, format='json')

    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    def test_api_can_get_json_from_file(self, mock):
        """ Test that the api can get a json from a .json file """
        # Arrange:
        mock_location = os.path.join(os.getcwd(), 'panels', 'tests')
        mock.return_value = mock_location
        # Act:
        client = self.authenticated_authorized_client
        response = self.target_request_from_client(client)
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

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )


class GetJsonFromFileIfKeyDoesNotExist(
    APITestBase, FileTestSetup, TestCase
):
    """ Test suite to test the api can not get a json
        if key does not exist
    """

    def setUp(self):
        """ Define the test suite setup """
        self.setTestFilesConfig()
        self.setCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('files-get-json')
        data = {
            'key': 'my_fake_key'
        }
        return client.get(url, data, format='json')

    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    def test_api_cannot_get_json_if_the_key_does_not_exist(self, mock):
        """ Test that the api cannot get a json if the key does not exist """
        mock_location = os.path.join(os.getcwd(), 'panels', 'tests')
        mock.return_value = mock_location
        # Act:
        client = self.authenticated_authorized_client
        response = self.target_request_from_client(client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'The server did retrieve a file'
        )

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )
