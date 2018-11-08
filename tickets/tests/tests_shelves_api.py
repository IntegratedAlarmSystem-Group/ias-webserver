import mock
import datetime
from freezegun import freeze_time
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from tickets.models import ShelveRegistry, ShelveRegistryStatus
from tickets.serializers import ShelveRegistrySerializer


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

    def _setup_common_users_and_clients(self):
        """ Add unauthenticated and unauthorized users """
        self.unauthorized_user = self.create_user(
            username='user', password='123', permissions=[])
        self.unauthenticated_client = APIClient()
        self.authenticated_unauthorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_unauthorized_client,
            Token.objects.get(user__username=self.unauthorized_user.username)
        )


class RequestAPIAuthTestCase(APITestBase):
    """ Base test case for a request with auth conditions """

    def test_api_cannot_allow_request_for_unauthenticated_user(self):
        """ The request should not be allowed for an unauthenticated user """
        client = self.unauthenticated_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Request not allowed for an unauthenticated user"
        )

    def test_api_cannot_allow_request_for_unauthorized_user(self):
        """ The request should not be allowed for an unauthorized user """
        client = self.authenticated_unauthorized_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Request not allowed for an unauthorized user"
        )


class RetrieveRegistry(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        """ Define the test suite setup """
        self._setup_common_users_and_clients()
        self.registry = ShelveRegistry.objects.create(
            alarm_id='alarm_1',
            message='Shelved because of reasons',
            timeout=datetime.timedelta(hours=2)
        )
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_shelveregistry'),
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse(
            'shelveregistry-detail', kwargs={'pk': self.registry.pk})
        return client.get(url, format='json')

    def test_api_can_retreive_registry_to_authorized_user(self):
        """ Test that the api should retrieve a ticket
            for an authorized user
        """
        # Act:
        expected_reg = ShelveRegistry.objects.get(pk=self.registry.pk)
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the registry'
        )
        self.assertEqual(
            self.response.data,
            ShelveRegistrySerializer(expected_reg).data
        )


class ListRegistry(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        """ Define the test suite setup """
        self._setup_common_users_and_clients()
        self.message = 'Shelved because of reasons'
        self.registry_1 = ShelveRegistry.objects.create(
            alarm_id='alarm_1',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2 = ShelveRegistry.objects.create(
            alarm_id='alarm_2',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2.unshelve()
        self.registry_3 = ShelveRegistry.objects.create(
            alarm_id='alarm_3',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_shelveregistry'),
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse('shelveregistry-list')
        return client.get(url, format='json')

    def test_api_can_list_registries(self):
        """ Test that the api can list the ShelveRegistries
            for an authorized user
        """

        registries = [
            self.registry_1,
            self.registry_2,
            self.registry_3
        ]
        expected_registries_data = [
            ShelveRegistrySerializer(t).data for t in registries]
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the registries'
        )
        retrieved_registries_data = self.response.data
        self.assertEqual(
            retrieved_registries_data,
            expected_registries_data,
            'The retrieved registries do not match the expected ones'
        )


class UpdateRegistry(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        """ Define the test suite setup """
        self._setup_common_users_and_clients()
        self.registry = ShelveRegistry.objects.create(
            alarm_id='alarm_1',
            message='Shelve because of reasons'
        )
        self.new_reg_data = {
            'alarm_id': self.registry.alarm_id,
            'message': 'Another message'
        }
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='change_shelveregistry')
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse(
            'shelveregistry-detail', kwargs={'pk': self.registry.pk})
        data = self.new_reg_data
        return client.put(url, data, format='json')

    def test_api_can_update_registry(self):
        """ Test that the api can update a registry
            for an authorized user
        """
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        updated_reg = ShelveRegistry.objects.get(
            alarm_id=self.registry.alarm_id
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The server did not update the registry'
        )
        self.assertEqual(
            {'alarm_id': updated_reg.alarm_id, 'message': updated_reg.message},
            self.new_reg_data,
            'The updated registry does not match the data sent in the request'
        )
        self.assertEqual(
            self.response.data,
            ShelveRegistrySerializer(updated_reg).data,
            'The response does not match the updated registry'
        )


class UpdateRegistryWithoutMessage(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        """ Define the test suite setup """
        self._setup_common_users_and_clients()
        self.registry = ShelveRegistry.objects.create(
            alarm_id='alarm_1',
            message='Shelve because of reasons'
        )
        self.new_reg_data = {
            'alarm_id': self.registry.alarm_id,
            'message': ''
        }
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='change_shelveregistry')
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse(
            'shelveregistry-detail', kwargs={'pk': self.registry.pk})
        data = self.new_reg_data
        return client.put(url, data, format='json')

    def test_api_cannot_update_registry_to_have_no_message(self):
        """ Test that the api cannot update a registry and leave it
            without a message for an authorized user
        """
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        updated_reg = ShelveRegistry.objects.get(
            alarm_id=self.registry.alarm_id
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'The server updated the registry'
        )
        self.assertEqual(
            {
                'alarm_id': updated_reg.alarm_id,
                'message': updated_reg.message
            },
            {
                'alarm_id': self.registry.alarm_id,
                'message': self.registry.message
            },
            'The the registry was updated with an empty message'
        )


class DeleteRegistry(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        """ Define the test suite setup """
        self._setup_common_users_and_clients()
        self.registry = ShelveRegistry.objects.create(
            alarm_id='alarm_1',
            message='Shelve because of reasons'
        )
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='delete_shelveregistry'),
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse(
            'shelveregistry-detail', kwargs={'pk': self.registry.pk})
        return client.delete(url, format='json')

    def test_api_can_delete_a_registry(self):
        """ Test that the api can delete a registry
            for an authorized user
        """
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        retrieved_reg = list(
            ShelveRegistry.objects.filter(pk=self.registry.pk)
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_204_NO_CONTENT,
            'The server did not delete the registry'
        )
        self.assertEqual(retrieved_reg, [], 'The registry was not deleted')


class FilterRegistryForAlarmAndShelvedCase(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        self._setup_common_users_and_clients()
        self.message = 'Shelved because of reasons'
        self.registry_1 = ShelveRegistry.objects.create(
            alarm_id='alarm_1',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2 = ShelveRegistry.objects.create(
            alarm_id='alarm_2',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2.unshelve()
        self.registry_3 = ShelveRegistry.objects.create(
            alarm_id='alarm_3',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.new_registry_2 = ShelveRegistry.objects.create(
            alarm_id=self.registry_2.alarm_id,
            message='New message',
            timeout=datetime.timedelta(hours=2)
        )
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_shelveregistry'),
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse('shelveregistry-filters')
        data = {
            'alarm_id': self.registry_2.alarm_id,
            'status': ShelveRegistryStatus.get_choices_by_name()['SHELVED']
        }
        return client.get(url, data, format='json')

    def test_api_can_filter_registries_by_alarms_and_shelve_status(self):
        """ Tets that the api can list the ShelveRegistrys filtered by alarm
            and shelved status for an authorized user
        """
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)

        expected_registries_data = [
            ShelveRegistrySerializer(self.new_registry_2).data
        ]
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the filtered registries'
        )
        retrieved_registries_data = self.response.data
        self.assertEqual(
            retrieved_registries_data,
            expected_registries_data,
            'The retrieved filtered registries do not match the expected ones'
        )


class FilterRegistryForAlarmAndUnshelvedCase(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        self._setup_common_users_and_clients()
        self.message = 'Shelved because of reasons'
        self.registry_1 = ShelveRegistry.objects.create(
            alarm_id='alarm_1',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2 = ShelveRegistry.objects.create(
            alarm_id='alarm_2',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2.unshelve()
        self.registry_3 = ShelveRegistry.objects.create(
            alarm_id='alarm_3',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.new_registry_2 = ShelveRegistry.objects.create(
            alarm_id=self.registry_2.alarm_id,
            message='New message'
        )
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_shelveregistry'),
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse('shelveregistry-filters')
        data = {
            'alarm_id': self.registry_2.alarm_id,
            'status': ShelveRegistryStatus.get_choices_by_name()[
                'UNSHELVED']
        }
        return client.get(url, data, format='json')

    def test_api_can_filter_registries_by_alarm_and_unshelved_status(self):
        """ Tets that the api can list the ShelveRegistrys filtered by
            alarm and unshelved status for an authorized user
        """
        # Arrange:
        expected_registries_data = [
            ShelveRegistrySerializer(self.registry_2).data
        ]
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the filtered registries'
        )
        retrieved_registries_data = self.response.data
        self.assertEqual(
            retrieved_registries_data,
            expected_registries_data,
            'The retrieved filtered registries do not match the expected ones'
        )


class FilterRegistryForShelvedCase(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        self._setup_common_users_and_clients()
        self.message = 'Shelved because of reasons'
        self.registry_1 = ShelveRegistry.objects.create(
            alarm_id='alarm_1',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2 = ShelveRegistry.objects.create(
            alarm_id='alarm_2',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2.unshelve()
        self.registry_3 = ShelveRegistry.objects.create(
            alarm_id='alarm_3',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_shelveregistry'),
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse('shelveregistry-filters')
        data = {
            'status': ShelveRegistryStatus.get_choices_by_name()['SHELVED']
        }
        return client.get(url, data, format='json')

    def test_api_can_filter_all_shelved_registries(self):
        """ Test that the api can filter ShelveRegistrys only by shelved status
            for an authenticated user
        """
        # Arrange:
        expected_registries_data = [
            ShelveRegistrySerializer(self.registry_1).data,
            ShelveRegistrySerializer(self.registry_3).data,
        ]
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the filtered registries'
        )
        retrieved_registries_data = self.response.data
        self.assertEqual(
            retrieved_registries_data,
            expected_registries_data,
            'The retrieved filtered registries do not match the expected ones'
        )


class FilterRegistryForUnshelvedCase(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        self._setup_common_users_and_clients()
        self.message = 'Shelved because of reasons'
        self.registry_1 = ShelveRegistry.objects.create(
            alarm_id='alarm_1',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2 = ShelveRegistry.objects.create(
            alarm_id='alarm_2',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2.unshelve()
        self.registry_3 = ShelveRegistry.objects.create(
            alarm_id='alarm_3',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_shelveregistry'),
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse('shelveregistry-filters')
        data = {
            'status': ShelveRegistryStatus.get_choices_by_name()[
                'UNSHELVED']
        }
        return client.get(url, data, format='json')

    def test_api_can_filter_all_open_registries(self):
        """ Test that the api can filter ShelveRegistrys by unshelved
            status for an authenticated user
        """
        # Arrange:
        expected_registries_data = [
            ShelveRegistrySerializer(self.registry_2).data,
        ]
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the filtered registries'
        )
        retrieved_registries_data = self.response.data
        self.assertEqual(
            retrieved_registries_data,
            expected_registries_data,
            'The retrieved filtered registries do not match the expected ones'
        )


class CreateRegistry(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        self._setup_common_users_and_clients()
        self.message = 'Shelved because of reasons'
        self.new_reg_data = {
            'alarm_id': 'alarm_4',
            'message': self.message,
            'timeout': '3:16:13'
        }
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='add_shelveregistry'),
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse('shelveregistry-list')
        data = self.new_reg_data
        return client.post(url, data, format='json')

    @mock.patch('tickets.connectors.AlarmConnector.shelve_alarm')
    def test_api_can_create_registry(self, AlarmConnector_shelve_alarm):
        """ Test that the api can create a registry """
        # Arrange
        AlarmConnector_shelve_alarm.return_value = 1
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_201_CREATED,
            'The server did not create the registry'
        )
        created_reg = ShelveRegistry.objects.get(
            alarm_id=self.new_reg_data['alarm_id']
        )
        retrieved_data = {
            'alarm_id': created_reg.alarm_id,
            'message': created_reg.message,
            'timeout': str(created_reg.timeout),
        }
        self.assertEqual(
            retrieved_data,
            self.new_reg_data,
            'The created registry does not match the data sent in the request'
        )
        self.assertEqual(
            self.response.data,
            ShelveRegistrySerializer(created_reg).data,
            'The response does not match the created registry'
        )
        self.assertTrue(
            AlarmConnector_shelve_alarm.called,
            'The alarm connector shelve method should have been called'
        )


class CreateRegistryWithNoMessageCase(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        self._setup_common_users_and_clients()
        self.new_reg_data = {
            'alarm_id': 'alarm_4',
        }
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='add_shelveregistry'),
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse('shelveregistry-list')
        data = self.new_reg_data
        return client.post(url, data, format='json')

    @mock.patch('tickets.connectors.AlarmConnector.shelve_alarm')
    @mock.patch('tickets.connectors.AlarmConnector.unshelve_alarms')
    def test_api_can_create_registry(
        self, AlarmConnector_shelve_alarm, AlarmConnector_unshelve_alarms
    ):
        """ Test that the api cannot create a registry without a message
            for an authorized user
        """
        # Arrange
        AlarmConnector_shelve_alarm.return_value = 1
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'The server created the registry'
        )
        created_reg = list(
            ShelveRegistry.objects.filter(
                alarm_id=self.new_reg_data['alarm_id'])
        )
        self.assertEqual(
            created_reg,
            [],
            'The registry was created'
        )
        self.assertTrue(
            AlarmConnector_unshelve_alarms.called,
            'The alarm connector unshelve method should have been called'
        )


class CreateRegistryAndNoShelvableAlarm(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        self._setup_common_users_and_clients()
        self.message = 'Shelved because of reasons'
        self.new_reg_data = {
            'alarm_id': 'alarm_4',
            'message': self.message,
            'timeout': '3:16:13'
        }
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='add_shelveregistry'),
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse('shelveregistry-list')
        data = self.new_reg_data
        return client.post(url, data, format='json')

    @mock.patch('tickets.connectors.AlarmConnector.shelve_alarm')
    def test_api_cannot_create_registry_for_non_shelvable_alarm(
        self, AlarmConnector_shelve_alarm
    ):
        """ Test that the api cannot create a registry
            to a non shelvable alarm for an authorized user """
        # Arrange
        AlarmConnector_shelve_alarm.return_value = -1
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            'The server did not forbid to create the registry'
        )
        created_reg = ShelveRegistry.objects.filter(
            alarm_id=self.new_reg_data['alarm_id']
        ).first()
        self.assertEqual(
            created_reg,
            None,
            'The registry was created'
        )
        self.assertTrue(
            AlarmConnector_shelve_alarm.called,
            'The alarm connector shelve method should have been called'
        )


class CreateRegistryAndAlreadyShelvedAlarm(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        self._setup_common_users_and_clients()
        self.message = 'Shelved because of reasons'
        self.new_reg_data = {
            'alarm_id': 'alarm_4',
            'message': self.message,
            'timeout': '3:16:13'
        }
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='add_shelveregistry'),
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse('shelveregistry-list')
        data = self.new_reg_data
        return client.post(url, data, format='json')

    @mock.patch('tickets.connectors.AlarmConnector.shelve_alarm')
    def test_api_cannot_create_registry_for_already_shelved_alarm(
        self, AlarmConnector_shelve_alarm
    ):
        """ Test that the api cannot create a registry
            to an already shelved alarm for an authorized user """
        # Arrange
        AlarmConnector_shelve_alarm.return_value = 0
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The server re-shelved the alarm'
        )
        created_reg = ShelveRegistry.objects.filter(
            alarm_id=self.new_reg_data['alarm_id']
        ).first()
        self.assertEqual(
            created_reg,
            None,
            'A new registry was created'
        )
        self.assertTrue(
            AlarmConnector_shelve_alarm.called,
            'The alarm connector shelve method should have been called'
        )


class UnshelveMultipleRegistries(RequestAPIAuthTestCase, TestCase):

    def setUp(self):
        """ Define the test suite setup """
        self._setup_common_users_and_clients()
        self.message = 'Shelved because of reasons'
        self.registry_1 = ShelveRegistry.objects.create(
            alarm_id='alarm_1',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2 = ShelveRegistry.objects.create(
            alarm_id='alarm_2',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2.unshelve()
        self.registry_3 = ShelveRegistry.objects.create(
            alarm_id='alarm_3',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='unshelve_shelveregistry'),
            ])
        self.authenticated_authorized_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_authorized_client,
            Token.objects.get(user__username=self.authorized_user.username)
        )

    def target_request_from_client(self, client):
        url = reverse('shelveregistry-unshelve')
        alarms_to_unshelve = ['alarm_1', 'alarm_2', 'alarm_3']
        data = {
            'alarms_ids': alarms_to_unshelve
        }
        return client.put(url, data, format='json')

    @mock.patch('tickets.connectors.AlarmConnector.unshelve_alarms')
    def test_api_can_unshelve_multiple_registries(
        self, AlarmConnector_unshelve_alarms
    ):
        """ Test that the api can unshelve multiple ununshelved
            registries for an authorized user """
        # Arrange
        expected_unshelved_alarms = ['alarm_1', 'alarm_3']
        # Act:
        self.response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The status of the response is incorrect'
        )
        self.assertEqual(
            self.response.data,
            expected_unshelved_alarms,
            'The response is not as expected'
        )
        unshelved_registries = [
            ShelveRegistry.objects.get(pk=self.registry_1.pk),
            ShelveRegistry.objects.get(pk=self.registry_3.pk)
        ]
        expected_status = int(
            ShelveRegistryStatus.get_choices_by_name()['UNSHELVED']
        )
        self.assertTrue(
            unshelved_registries[0].status == expected_status and
            unshelved_registries[1].status == expected_status,
            'The registries were not correctly unshelved'
        )
        self.assertNotEqual(
            unshelved_registries[0].unshelved_at, None,
            'The first registry unshelving time was not correctly recorded'
        )
        self.assertNotEqual(
            unshelved_registries[1].unshelved_at, None,
            """ The second registry unshelving time
                was not correctly recorded
            """
        )
        self.assertTrue(
            AlarmConnector_unshelve_alarms.called,
            'The alarm connector unshelve method should have been called'
        )


class ApiCanCheckTimeouts(APITestBase, TestCase):

    def setUp(self):
        """ Define the test suite setup """
        self.message = 'Shelved because of reasons'
        self.registry_1 = ShelveRegistry.objects.create(
            alarm_id='alarm_1',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2 = ShelveRegistry.objects.create(
            alarm_id='alarm_2',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.registry_2.unshelve()
        self.registry_3 = ShelveRegistry.objects.create(
            alarm_id='alarm_3',
            message=self.message,
            timeout=datetime.timedelta(hours=2)
        )
        self.nopermissions_user = self.create_user(
            username='user', password='123', permissions=[])
        self.unauthenticated_client = APIClient()

    def target_request_from_client(self, client):
        url = reverse('shelveregistry-check-timeouts')
        return client.put(url, format='json')

    @mock.patch('tickets.connectors.AlarmConnector.unshelve_alarms')
    def test_api_can_check_timeouts_for_an_unauthenticated_client(
        self,
        AlarmConnector_unshelve_alarms
    ):
        """ Test that the api can check if active registries have timed out
            and notify accordingly for an authenticated user """
        # Arrange:
        shelving_time = timezone.now()
        checking_time = shelving_time + datetime.timedelta(hours=2)
        with freeze_time(shelving_time):
            self.registries = [
                self.registry_1,
                self.registry_2,
                self.registry_3,
                ShelveRegistry.objects.create(
                    alarm_id='alarm_4',
                    message=self.message,
                    timeout=datetime.timedelta(hours=4)
                ),
                ShelveRegistry.objects.create(
                    alarm_id='alarm_5',
                    message=self.message,
                    timeout=datetime.timedelta(hours=1)
                ),
            ]
        expected_timedout = ['alarm_1', 'alarm_3', 'alarm_5']
        expected_status = ShelveRegistryStatus.get_choices_by_name()[
            'UNSHELVED']

        # Act:
        with freeze_time(checking_time):
            self.response = self.target_request_from_client(
                self.unauthenticated_client)

        # Assert:
        unshelved_registries = list(
            ShelveRegistry.objects.filter(status=expected_status)
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The status of the response is incorrect'
        )
        self.assertEqual(
            self.response.data,
            expected_timedout,
            'The response is not as expected'
        )
        for reg in unshelved_registries:
            self.assertTrue(
                reg.status == expected_status,
                'The registries were not correctly unshelved'
            )
            self.assertNotEqual(
                reg.unshelved_at, None,
                'The regitries unshelving time was not correctly recorded'
            )
        self.assertTrue(
            AlarmConnector_unshelve_alarms.called,
            'The alarm connector unshelve method should have been called'
        )
        AlarmConnector_unshelve_alarms.assert_called_with(expected_timedout)
