from django.test import TestCase
from users.models import reset_auth_token
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class UserTestCase(TestCase):
    """This class defines the test case for user related functions"""

    def test_auth_token_should_be_create_if_new_user(self):
        """ Test if token is created for new users """
        user = User.objects.create_user(
            'username', password='123', email='user@user.cl')
        query = Token.objects.filter(user__username=user.username)
        self.assertEqual(query.count(), 1, 'Unexpected token count')

    def test_reset_auth_token_function(self):
        """ Test function to reset the auth token for a user """
        # Arrange:
        user = User.objects.create_user(
            'username', password='123', email='user@user.cl')
        q = Token.objects.filter(user__username=user.username)
        self.assertEqual(q.count(), 1, 'Unexpected token count')
        token = q.first()
        token_key = token.key
        # Act:
        reset_auth_token(user)
        # Assert:
        q = Token.objects.filter(user__username=user.username)
        self.assertEqual(q.count(), 1, 'Unexpected token count after reset')
        current_token = q.first()
        current_token_key = current_token.key
        self.assertNotEqual(
            current_token_key, token_key, 'User should have a new token')
