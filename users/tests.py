from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

# Create your tests here.


class AuthApiTestCase(TestCase):
    """Test suite for users' authentication."""

    def setUp(self):
        """Define the test suite setup"""
        self.client = APIClient()
        self.username = 'test'
        self.user = User.objects.create_user(
            username=self.username, password='password', email='test@user.cl')
        self.token = Token.objects.get(user__username=self.username)

    def test_user_login(self):
        """ Test that an user can request a token using name and password """
        url = reverse('get-token')
        data = {'username': 'test', 'password': 'password'}
        response = self.client.post(url, data, format='json')
        json_response = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json_response['token'], self.token.key)
