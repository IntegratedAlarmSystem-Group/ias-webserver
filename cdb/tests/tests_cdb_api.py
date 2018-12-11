from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.urls import reverse
from cdb.readers import CdbReader


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


class ListIasConfigurationData(APITestBase, TestCase):
    """Test suite to test the list request for the ias configuration"""

    def setUp(self):
        """Define the test suite setup"""
        # unauthenticated client
        self.unauthenticated_client = APIClient()
        # authenticated client
        self.nopermissions_user = self.create_user(
            username='authorized',
            password='123',
            permissions=[]
        )
        client = APIClient()
        self.authenticate_client_using_token(
            client, Token.objects.get(
                user__username=self.nopermissions_user.username)
        )
        self.authenticated_client = client

    def target_request_from_client(self, client):
        url = reverse('ias')
        return client.get(url, format='json')

    def test_api_can_list_ias_for_an_authenticated_user(self):
        """ Test that the api can retrieve an Ias
            for an authenticated user without specific permissions
        """
        # Arrange:
        expected_ias_data = CdbReader.read_ias()
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_client
        )
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the ias'
        )
        retrieved_ias_data = self.response.data
        self.assertEqual(
            retrieved_ias_data,
            expected_ias_data,
            'The retrieved ias does not match the expected'
        )

    def test_api_cannot_allow_the_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )


class RetrieveIasConfigurationData(APITestBase, TestCase):
    """Test suite to test the get request for the ias configuration"""

    def setUp(self):
        """Define the test suite setup"""
        # unauthenticated client
        self.unauthenticated_client = APIClient()
        # authenticated client
        self.nopermissions_user = self.create_user(
            username='authorized',
            password='123',
            permissions=[]
        )
        client = APIClient()
        self.authenticate_client_using_token(
            client, Token.objects.get(
                user__username=self.nopermissions_user.username)
        )
        self.authenticated_client = client

    def target_request_from_client(self, client):
        url = reverse('ias')
        return client.get(url, kwargs={'pk': 0}, format="json")

    def test_api_can_get_ias_for_authenticated_user(self):
        """ Test that the api can retrieve an Ias
            for an authenticated user without specific permissions
        """
        # Arrange:
        expected_ias_data = CdbReader.read_ias()
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_client
        )
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the ias'
        )
        retrieved_ias_data = self.response.data
        self.assertEqual(
            retrieved_ias_data,
            expected_ias_data,
            'The retrieved ias does not match the expected'
        )

    def test_api_cannot_allow_the_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )
