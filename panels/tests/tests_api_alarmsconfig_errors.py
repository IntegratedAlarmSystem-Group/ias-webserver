from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission
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


class AlarmsConfigErrorResponseTestSetUp:
    """Class to manage the common setup for testing."""

    def setTestAlarmsConfigErrorResponse(self):
        """ Method to set the alarms config for testing """

        self.placemark_type = PlacemarkType.objects.create(name='pad')
        self.placemark = Placemark.objects.create(
            name="placemark_1",
            type=self.placemark_type
        )

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


class WeatherConfigErrorResponse(
    APITestBase, AlarmsConfigErrorResponseTestSetUp, TestCase
):
    """ Test suite for the error responses in case of bad configuration """

    def setUp(self):
        """ Define the test suite setup """
        self.setTestAlarmsConfigErrorResponse()
        self.setCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_alarmconfig'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('alarmconfig-weather-config')
        return client.get(url, format='json')

    def test_api_weather_config_response_errors(self):
        """ Test that the api return error code if there is no weather data """
        self.client = self.authenticated_authorized_client
        # Act:
        response = self.target_request_from_client(self.client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If the view weather does not exist the api must return a 404 code'
        )
        # Act:
        weather_view = View.objects.create(name='weather')
        response = self.target_request_from_client(self.client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If the type station does not exist the api must return a 404 code'
        )
        # Act:
        station_type = Type.objects.create(name='station')
        response = self.target_request_from_client(self.client)
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
        response = self.target_request_from_client(self.client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'If there is weather config the api must return a 200 code'
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


class WeatherSummaryConfigErrorResponse(
    APITestBase, AlarmsConfigErrorResponseTestSetUp, TestCase
):
    """ Test suite for the error responses in case of bad configuration """

    def setUp(self):
        """ Define the test suite setup """
        self.setTestAlarmsConfigErrorResponse()
        self.setCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_alarmconfig'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('alarmconfig-weather-summary-config')
        return client.get(url, format='json')

    def test_api_weather_summary_config_response_errors(self):
        """Test that the api returns error code if there is no summary data"""
        self.client = self.authenticated_authorized_client
        # Act:
        response = self.target_request_from_client(self.client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If the view summary does not exist the api should return a 404'
        )
        # Act:
        summary_view = View.objects.create(name='summary')
        response = self.target_request_from_client(self.client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If there is not temperature, windspeed or humidity config the api \
             should return a 404'
        )
        # Act:
        temperature_type = Type.objects.create(name='temperature')
        response = self.target_request_from_client(self.client)
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
        response = self.target_request_from_client(self.client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'If there is any of temperature, windspeed or humidity config \
             for the summary view the api should return a 200'
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


class AntennasConfigErrorResponse(
    APITestBase, AlarmsConfigErrorResponseTestSetUp, TestCase
):
    """ Test suite for the error responses in case of bad configuration """

    def setUp(self):
        """ Define the test suite setup """
        self.setTestAlarmsConfigErrorResponse()
        self.setCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_alarmconfig'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('alarmconfig-antennas-config')
        return client.get(url, format='json')

    def test_api_antennas_config_response_errors(self):
        """Test that the api returns error code if there is no antennas data"""
        self.client = self.authenticated_authorized_client
        # Act:
        response = self.target_request_from_client(self.client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If the view antennas does not exist the api should return a 404'
        )
        # Act:
        antennas_view = View.objects.create(name='antennas')
        response = self.target_request_from_client(self.client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If the type antenna does not exist the api should return a 404'
        )
        # Act:
        antenna_type = Type.objects.create(name='antenna')
        response = self.target_request_from_client(self.client)
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
        response = self.target_request_from_client(self.client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'If there is antennas config the api must return a 200 code'
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


class AntennasSummaryConfigErrorResponse(
    APITestBase, AlarmsConfigErrorResponseTestSetUp, TestCase
):
    """ Test suite for the error responses in case of bad configuration """

    def setUp(self):
        """ Define the test suite setup """
        self.setTestAlarmsConfigErrorResponse()
        self.setCommonUsersAndClients()

        self.authorized_user = self.create_user(
            username='authorized', password='123',
            permissions=[
                Permission.objects.get(codename='view_alarmconfig'),
            ])
        client = APIClient()
        self.authenticate_client_using_token(
            client,
            Token.objects.get(user__username=self.authorized_user.username)
        )
        self.authenticated_authorized_client = client

    def target_request_from_client(self, client):
        url = reverse('alarmconfig-antennas-summary-config')
        return client.get(url, format='json')

    def test_api_antennas_summary_config_response_errors(self):
        """Test that the api returns error code if there is no summary data"""
        self.client = self.authenticated_authorized_client
        # Act:
        response = self.target_request_from_client(self.client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'If the view summary does not exist the api should return a 404'
        )
        # Act:
        summary_view = View.objects.create(name='summary')
        antenna_type = Type.objects.create(name='antenna')
        response = self.target_request_from_client(self.client)
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
        response = self.target_request_from_client(self.client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'If there is antennas config for the summary view \
             the api should return a 200'
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
