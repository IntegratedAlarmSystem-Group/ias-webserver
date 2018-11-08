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


class CdbApiTestCase(APITestBase, TestCase):
    """Test suite for the api views."""

    def setUp(self):
        """Define the test suite setup"""
        self.no_permissions_user = self.create_user(
            username='user', password='123', permissions=[])
        self.authenticated_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_client,
            Token.objects.get(user__username=self.no_permissions_user)
        )
        self.client = self.authenticated_client

    def test_api_can_list_ias(self):
        """ Test that the api can retrieve an Ias """
        # Arrange:
        expected_ias_data = CdbReader.read_ias()
        # Act:
        url = reverse('ias')
        self.response = self.client.get(url, format="json")
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

    def test_api_can_get_ias(self):
        """ Test that the api can retrieve an Ias """
        # Arrange:
        expected_ias_data = CdbReader.read_ias()
        # Act:
        url = reverse('ias')
        self.response = self.client.get(url, kwargs={'pk': 0}, format="json")
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
