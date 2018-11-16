from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from users.serializers import UserSerializer


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

    def create_group(self, **kwargs):
        """ Creates a group """
        users = kwargs.get('users', [])
        name = kwargs.get('name', 'group')
        group, created = Group.objects.get_or_create(name=name)
        for user in users:
            group.user_set.add(user)
        return group

    def authenticate_client_using_token(self, client, token):
        """ Authenticates a selected API Client using a related User token """
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)


class UsersTestSetup:
    """Class to manage the common setup for testing."""

    def setupGroups(self):
        """ Add groups and users belonging different groups """
        self.user_1 = User.objects.create_user('user_1', '123', 'user@user.cl')
        self.user_2 = User.objects.create_user('user_2', '123', 'user@user.cl')
        self.user_3 = User.objects.create_user('user_3', '123', 'user@user.cl')
        self.user_4 = User.objects.create_user('user_4', '123', 'user@user.cl')

        self.group_1 = self.create_group(
            name='group_1',
            users=[self.user_1, self.user_2]
        )
        self.group_2 = self.create_group(
            name='group_2',
            users=[self.user_3, self.user_4]
        )

    def setupCommonUsersAndClients(self):
        """ Add unauthenticated and unauthorized users """
        self.unauthorized_user = self.create_user(
            username='user', password='123', permissions=[])
        self.unauthenticated_client = APIClient()
        self.authenticated_unauthorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_unauthorized_client,
            Token.objects.get(user__username=self.unauthorized_user.username)
        )


class RetrieveUsersByGroup(APITestBase, UsersTestSetup, TestCase):
    """Test suite to test the retrieve request"""

    def setUp(self):
        """Define the test suite setup"""
        self.setupGroups()
        self.setupCommonUsersAndClients()

        # self.authorized_user = self.create_user(
        #     username='authorized', password='123',
        #     permissions=[
        #         Permission.objects.get(codename='view_'),
        #     ])
        # client = APIClient()
        # self.authenticate_client_using_token(
        #     client,
        #     Token.objects.get(user__username=self.authorized_user.username)
        # )
        # self.authenticated_authorized_client = client

    def test_api_can_retrieve_users_by_group(self):
        """The api should retrieve the list of users beloging to a group"""

        # Arrange:
        users = [
            User.objects.get(pk=self.user_1.pk),
            User.objects.get(pk=self.user_2.pk)
        ]
        expected_users_data = [UserSerializer(u).data for u in users]

        # Act:
        client = self.authenticated_unauthorized_client
        url = reverse('user-filters')
        data = {'group': 'group_1'}
        self.response = client.get(url, data, format="json")

        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The server should retrieve a 200 status'
        )
        print(self.response.data)
        self.assertEqual(
            self.response.data,
            expected_users_data,
            'The server should retrieve the expected ticket'
        )
