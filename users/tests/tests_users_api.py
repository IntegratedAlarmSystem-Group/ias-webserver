from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission


class APITestBase:

    def create_group(self, **kwargs):
        """ Creates a group with permissions """
        users = kwargs.get('users', [])
        name = kwargs.get('name', 'group')
        group = Group.objects.get_or_create(name=name)
        for user in users:
            group.user_set.add(user)
        return group

    def authenticate_client_using_token(self, client, token):
        """ Authenticates a selected API Client using a related User token """
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)


class UsersTestSetup:
    """Class to manage the common setup for testing."""

    def setupCommonUsersAndClients(self):
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

        # self.unauthenticated_client = APIClient()
        # self.authenticated_unauthorized_client = APIClient()
        # self.authenticate_client_using_token(
        #     self.authenticated_unauthorized_client,
        #     Token.objects.get(user__username=self.unauthorized_user.username)
        # )
