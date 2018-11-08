from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from panels.models import (
    AlarmConfig,
    View,
    Type,
    Placemark,
    PlacemarkType,
    PlacemarkGroup
)


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


class PlacemarkApiTestCase(APITestBase, TestCase):
    """ Test suite for the placemarks api """

    def setUp(self):
        """ Define the test suite setup """
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
        self.antenna_type = Type.objects.create(name='antenna')
        self.antennas_view = View.objects.create(name='antennas')
        self.antennas_alarms_config = [
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_1",
                view=self.antennas_view,
                type=self.antenna_type,
                placemark=self.placemarks[0],
                custom_name="A001",
                tags="group_A"
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_2",
                view=self.antennas_view,
                type=self.antenna_type,
                placemark=self.placemarks[1],
                custom_name="A002",
                tags="group_A"
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_3",
                view=self.antennas_view,
                type=self.antenna_type,
                custom_name="A003",
                tags="group_B"
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_4",
                view=self.antennas_view,
                type=self.antenna_type,
                placemark=self.placemarks[3],
                custom_name="A004",
                tags="group_A"
            ),
        ]

        self.no_permissions_user = self.create_user(
            username='user', password='123', permissions=[])
        self.authenticated_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_client,
            Token.objects.get(user__username=self.no_permissions_user)
        )
        self.client = self.authenticated_client

    def test_api_can_get_pads_by_group(self):
        """ Test can retrieve the pads by group in the required format """
        # Arrange:
        expected_response = {
            "GROUP1": {
                "PAD1": "A001"
            }
        }

        # Act:
        url = reverse('placemark-pads-by-group')
        data = {'group': "GROUP1"}
        response = self.client.get(url, data, format='json')

        # Assert:
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

    def test_api_can_get_pads_by_group_without_group(self):
        """ Test can retrieve the pads without group in the required format """
        # Arrange:
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
        url = reverse('placemark-pads-by-group')
        response = self.client.get(url, format='json')

        # Assert:
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
