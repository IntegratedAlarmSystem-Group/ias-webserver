import os
import mock
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from panels.models import (
    LocalAlarmConfig,
    Placemark,
    PlacemarkType,
    PlacemarkGroup
)

MOCK_FILES_PATH = os.path.join(os.getcwd(), 'panels', 'tests')


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


class PlacemarksTestSetUp:
    """Class to manage the common setup for testing."""

    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    def setTestPlacemarksConfig(self, mock):
        mock.return_value = MOCK_FILES_PATH
        self.placemark_type = PlacemarkType.objects.create(name='pad')
        self.placemark_groups = [
            PlacemarkGroup.objects.create(name='GROUP1'),
            PlacemarkGroup.objects.create(name='GROUP2')
        ]
        self.placemarks = [
            Placemark.objects.create(
                name="PAD1",
                type=self.placemark_type,
                group=self.placemark_groups[0]
            ),
            Placemark.objects.create(
                name="PAD2",
                type=self.placemark_type,
                group=self.placemark_groups[1]
            ),
            Placemark.objects.create(
                name="PAD3",
                type=self.placemark_type,
                group=self.placemark_groups[1]
            ),
            Placemark.objects.create(
                name="PAD4",
                type=self.placemark_type
            ),
        ]
        self.antennas_to_pads_values = {
            "A001": "PAD1",
            "A002": "PAD2",
            "A004": "PAD4",
        }
        antennas_configurations_values = [
            {
                "alarm_id": "antennas_alarm_1",
                "custom_name": "A001",
                "type": "antenna",
                "view": "antennas",
                "placemark": "A001",
                "group": "group_A",
                "children": []
            },
            {
                "alarm_id": "antennas_alarm_2",
                "custom_name": "A002",
                "type": "antenna",
                "view": "antennas",
                "placemark": "A002",
                "group": "group_A",
                "children": []
            },
            {
                "alarm_id": "antennas_alarm_3",
                "custom_name": "A003",
                "type": "antenna",
                "view": "antennas",
                "placemark": "",
                "group": "group_B",
                "children": []
            },
            {
                "alarm_id": "antennas_alarm_4",
                "custom_name": "A004",
                "type": "antenna",
                "view": "antennas",
                "placemark": "A004",
                "group": "group_A",
                "children": []
            }
        ]
        self.antennas_configurations = [
            LocalAlarmConfig(e) for e in antennas_configurations_values
        ]
        updated_antennas_configurations_values = []
        for conf in antennas_configurations_values:
            updated_conf = {}
            for key, value in conf.items():
                if key is not 'placemark':
                    updated_conf[key] = conf[key]
                else:
                    if conf[key].strip() is not "":
                        updated_conf[key] = self.antennas_to_pads_values[
                            conf[key]
                        ]
                    else:
                        updated_conf[key] = conf[key]
            updated_antennas_configurations_values.append(updated_conf)
        self.updated_antennas_configurations = [
            LocalAlarmConfig(e) for e in updated_antennas_configurations_values
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


class RetrievePadsBySelectedGroup(
    APITestBase, PlacemarksTestSetUp, TestCase
):
    """ Test suite to test the retrieve of pads according to a selected group
    """

    def setUp(self):
        """ Define the test suite setup """
        self.setTestPlacemarksConfig()
        self.setCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_placemark'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('placemark-pads-by-group')
        data = {'group': "GROUP1"}
        return client.get(url, data, format='json')

    @mock.patch(
        'panels.models.LocalAlarmConfig.objects.get_file_configurations')
    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    @mock.patch('panels.connectors.ValueConnector.get_antennas_to_pad_values')
    def test_api_can_get_pads_by_group(
        self,
        mock_antennas_to_pad_values,
        mock_files_location,
        mock_get_antennas_configurations
    ):
        """ Test can retrieve the pads by group in the required format """
        # Arrange:
        mock_files_location.return_value = MOCK_FILES_PATH
        mock_antennas_to_pad_values.return_value = self.antennas_to_pads_values
        mock_a_configurations = self.updated_antennas_configurations
        mock_get_antennas_configurations.return_value = mock_a_configurations

        expected_response = {
            "GROUP1": {
                "PAD1": "A001"
            }
        }
        # Act:
        self.client = self.authenticated_authorized_client
        response = self.target_request_from_client(self.client)
        # Assert:
        mock_get_antennas_configurations.assert_called_with(
            'antennas_config',
            update_placemark_values=self.antennas_to_pads_values
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the pads'
        )
        retrieved_pads_data = response.data
        self.assertEqual(
            retrieved_pads_data,
            expected_response,
            'The retrieved pads do not match the expected ones'
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

    def test_api_cannot_allow_request_for_unauthorized_user(self):
        """ The request should not be allowed for an unauthorized user """
        client = self.authenticated_unauthorized_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Request not allowed for an unauthorized user"
        )


class RetrievePadsByGroup(
    APITestBase, PlacemarksTestSetUp, TestCase
):
    """ Test suite to test the retrieve of pads by group
        without selecting a group
    """

    def setUp(self):
        """ Define the test suite setup """
        self.setTestPlacemarksConfig()
        self.setCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_placemark'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('placemark-pads-by-group')
        return client.get(url, format='json')

    @mock.patch(
        'panels.models.LocalAlarmConfig.objects.get_file_configurations')
    @mock.patch('panels.models.FileManager._get_files_absolute_location')
    @mock.patch('panels.connectors.ValueConnector.get_antennas_to_pad_values')
    def test_api_can_get_pads_by_group_without_group(
        self,
        mock_antennas_to_pad_values,
        mock_files_location,
        mock_get_antennas_configurations
    ):
        """ Test can retrieve the pads without group in the required format """
        # Arrange:
        mock_files_location.return_value = MOCK_FILES_PATH
        mock_antennas_to_pad_values.return_value = self.antennas_to_pads_values
        mock_a_configurations = self.updated_antennas_configurations
        mock_get_antennas_configurations.return_value = mock_a_configurations

        expected_response = {
            "GROUP1": {
                "PAD1": "A001"
            },
            "GROUP2": {
                "PAD2": "A002",
                "PAD3": None
            },
            "other": {
                "PAD4": "A004"
            }
        }

        # Act:
        self.client = self.authenticated_authorized_client
        response = self.target_request_from_client(self.client)

        # Assert:
        mock_get_antennas_configurations.assert_called_with(
            'antennas_config',
            update_placemark_values=self.antennas_to_pads_values
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the pads'
        )
        retrieved_pads_data = response.data
        self.assertEqual(
            retrieved_pads_data,
            expected_response,
            'The retrieved pads do not match the expected ones'
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

    def test_api_cannot_allow_request_for_unauthorized_user(self):
        """ The request should not be allowed for an unauthorized user """
        client = self.authenticated_unauthorized_client
        self.response = self.target_request_from_client(client)
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Request not allowed for an unauthorized user"
        )
