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
            username=self.username,
            password='password',
            email='test@user.cl',
            first_name='First',
            last_name='Last',
        )
        self.token = Token.objects.get(user__username=self.username)

    def test_user_login(self):
        """ Test that an user can request a token using name and password """
        url = reverse('get-token')
        data = {'username': 'test', 'password': 'password'}
        response = self.client.post(url, data, format='json')
        json_response = response.json()
        expected_user_data = {
            'username': 'test',
            'email': 'test@user.cl',
            'first_name': 'First',
            'last_name': 'Last',
            'groups': []
        }
        expected_allowed_actions = {
            'can_ack': self.user.has_perm('tickets.acknowledge_ticket'),
            'can_shelve': self.user.has_perm('tickets.add_shelveregistry'),
            'can_unshelve':
            self.user.has_perm('tickets.unshelve_shelveregistry')
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json_response['token'], self.token.key,
            'The token is not the user token'
        )
        self.assertEqual(
            json_response['user_data'], expected_user_data,
            'The user_data is not as expected'
        )
        self.assertEqual(
            json_response['allowed_actions'], expected_allowed_actions,
            'Allowed actions are not as expected'
        )
