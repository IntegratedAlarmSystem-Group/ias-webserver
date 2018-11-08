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
    PlacemarkType
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


class AlarmConfigApiErrorResponsesTestCase(APITestBase, TestCase):
    """ Test suite for the error responses in case of bad configuration """

    def setUp(self):
        """ Define the test suite setup """
        self.placemark_type = PlacemarkType.objects.create(name='pad')
        self.placemark = Placemark.objects.create(
            name="placemark_1",
            type=self.placemark_type
        )
        self.no_permissions_user = self.create_user(
            username='user', password='123', permissions=[])
        self.authenticated_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_client,
            Token.objects.get(user__username=self.no_permissions_user)
        )
        self.client = self.authenticated_client

    def test_api_weather_config_response_errors(self):
        """ Test that the api return error code if there is no weather data """
        # Act:
        url = reverse('alarmconfig-weather-config')
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If the view weather does not exist the api must return a 404 code'
        )
        # Act:
        weather_view = View.objects.create(name='weather')
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If the type station does not exist the api must return a 404 code'
        )
        # Act:
        station_type = Type.objects.create(name='station')
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If there is not weather config the api must return a 404 code'
        )
        # Act:
        AlarmConfig.objects.create(
            alarm_id="station_alarm_1",
            view=weather_view,
            type=station_type,
            placemark=self.placemark
        )
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'If there is weather config the api must return a 200 code'
        )

    def test_api_antennas_config_response_errors(self):
        """Test that the api returns error code if there is no antennas data"""
        # Act:
        url = reverse('alarmconfig-antennas-config')
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If the view antennas does not exist the api should return a 404'
        )
        # Act:
        antennas_view = View.objects.create(name='antennas')
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If the type antenna does not exist the api should return a 404'
        )
        # Act:
        antenna_type = Type.objects.create(name='antenna')
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If the there is not antennas config the api should return a 404'
        )
        # Act:
        AlarmConfig.objects.create(
            alarm_id="antenna_alarm_1",
            view=antennas_view,
            type=antenna_type,
            placemark=self.placemark,
            custom_name="A001",
            tags="group_A"
        )
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'If there is antennas config the api must return a 200 code'
        )

    def test_api_antennas_summary_config_response_errors(self):
        """Test that the api returns error code if there is no summary data"""
        # Act:
        url = reverse('alarmconfig-antennas-summary-config')
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If the view summary does not exist the api should return a 404'
        )
        # Act:
        summary_view = View.objects.create(name='summary')
        antenna_type = Type.objects.create(name='antenna')
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If there is not antennas config for the summary the api \
             should return a 404'
        )
        # Act:
        AlarmConfig.objects.create(
            alarm_id="antennas_summary",
            view=summary_view,
            type=antenna_type
        )
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'If there is antennas config for the summary view \
             the api should return a 200'
        )

    def test_api_weather_summary_config_response_errors(self):
        """Test that the api returns error code if there is no summary data"""
        # Act:
        url = reverse('alarmconfig-weather-summary-config')
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If the view summary does not exist the api should return a 404'
        )
        # Act:
        summary_view = View.objects.create(name='summary')
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If there is not temperature, windspeed or humidity config the api \
             should return a 404'
        )
        # Act:
        temperature_type = Type.objects.create(name='temperature')
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If there is not temperature, windspeed or humidity configuration \
             for the summary view the api should return a 404'
        )
        # Act:
        AlarmConfig.objects.create(
            alarm_id="weather_summary_temp",
            view=summary_view,
            type=temperature_type
        )
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'If there is any of temperature, windspeed or humidity config \
             for the summary view the api should return a 200'
        )
