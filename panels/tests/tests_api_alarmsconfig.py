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


class AlarmsConfigTestSetUp:
    """Class to manage the common setup for testing."""

    def setTestAlarmsConfig(self):
        """ Method to set the alarms config for testing """

        self.temperature_type = Type.objects.create(name='temperature')
        self.humidity_type = Type.objects.create(name='humidity')
        self.windspeed_type = Type.objects.create(name='windspeed')
        self.station_type = Type.objects.create(name='station')
        self.antenna_type = Type.objects.create(name='antenna')
        self.fire_type = Type.objects.create(name='fire')
        self.fire_sys_type = Type.objects.create(name='fire_malfunction')
        self.ups_type = Type.objects.create(name='ups')
        self.hvac_type = Type.objects.create(name='hvac')
        self.power_type = Type.objects.create(name='power')
        self.health_type = Type.objects.create(name='health')
        self.weather_view = View.objects.create(name='weather')
        self.antennas_view = View.objects.create(name='antennas')
        self.summary_view = View.objects.create(name='summary')
        self.placemark_type = PlacemarkType.objects.create(name='pad')
        self.placemark_groups = [
            PlacemarkGroup.objects.create(name='group1'),
            PlacemarkGroup.objects.create(name='group2')
        ]

        self.placemarks = [
            Placemark.objects.create(
                name="placemark_station_1",
                type=self.placemark_type,
                group=self.placemark_groups[0]
            ),
            Placemark.objects.create(
                name="placemark_station_2",
                type=self.placemark_type,
                group=self.placemark_groups[1]

            ),
            Placemark.objects.create(
                name="placemark_pad_1",
                type=self.placemark_type
            ),
            Placemark.objects.create(
                name="placemark_pad_2",
                type=self.placemark_type
            ),
            Placemark.objects.create(
                name="placemark_pad_3",
                type=self.placemark_type
            ),
        ]
        self.stations_alarms_config = [
            AlarmConfig.objects.create(
                alarm_id="station_alarm_1",
                view=self.weather_view,
                type=self.station_type,
                placemark=self.placemarks[0]
            ),
            AlarmConfig.objects.create(
                alarm_id="station_alarm_2",
                view=self.weather_view,
                type=self.station_type,
                placemark=self.placemarks[1]
            )
        ]
        self.sensors_alarms_config = [
            AlarmConfig.objects.create(
                alarm_id="temperature_alarm_1",
                view=self.weather_view,
                type=self.temperature_type,
                parent=self.stations_alarms_config[0]
            ),
            AlarmConfig.objects.create(
                alarm_id="humidity_alarm_1",
                view=self.weather_view,
                type=self.humidity_type,
                parent=self.stations_alarms_config[0]
            ),
            AlarmConfig.objects.create(
                alarm_id="windspeed_alarm_1",
                view=self.weather_view,
                type=self.windspeed_type,
                parent=self.stations_alarms_config[0]
            ),
            AlarmConfig.objects.create(
                alarm_id="temperature_alarm_2",
                view=self.weather_view,
                type=self.temperature_type,
                parent=self.stations_alarms_config[1]
            ),
            AlarmConfig.objects.create(
                alarm_id="humidity_alarm_2",
                view=self.weather_view,
                type=self.humidity_type,
                parent=self.stations_alarms_config[1]
            ),
            AlarmConfig.objects.create(
                alarm_id="windspeed_alarm_2",
                view=self.weather_view,
                type=self.windspeed_type,
                parent=self.stations_alarms_config[1]
            ),
        ]
        self.antennas_alarms_config = [
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_1",
                view=self.antennas_view,
                type=self.antenna_type,
                placemark=self.placemarks[2],
                custom_name="A001",
                tags="group_A"
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_2",
                view=self.antennas_view,
                type=self.antenna_type,
                placemark=self.placemarks[3],
                custom_name="A002",
                tags="group_A"
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_3",
                view=self.antennas_view,
                type=self.antenna_type,
                placemark=self.placemarks[4],
                custom_name="A003",
                tags="group_B"
            )
        ]
        self.antennas_devices_alarms_config = [
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_1_fire",
                view=self.antennas_view,
                type=self.fire_type,
                custom_name="Fire",
                parent=self.antennas_alarms_config[0]
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_1_fire_malfunction",
                view=self.antennas_view,
                type=self.fire_sys_type,
                custom_name="Fire Malfunction",
                parent=self.antennas_alarms_config[0]
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_1_ups",
                view=self.antennas_view,
                type=self.ups_type,
                custom_name="UPS",
                parent=self.antennas_alarms_config[0]
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_1_hvac",
                view=self.antennas_view,
                type=self.hvac_type,
                custom_name="HVAC",
                parent=self.antennas_alarms_config[0]
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_1_power",
                view=self.antennas_view,
                type=self.power_type,
                custom_name="Power",
                parent=self.antennas_alarms_config[0]
            ),
        ]
        self.summary_alarms_config = [
            AlarmConfig.objects.create(
                alarm_id="antennas_summary",
                view=self.summary_view,
                type=self.antenna_type
            ),
            AlarmConfig.objects.create(
                alarm_id="weather_summary_temp",
                view=self.summary_view,
                type=self.temperature_type
            ),
            AlarmConfig.objects.create(
                alarm_id="weather_summary_hum",
                view=self.summary_view,
                type=self.humidity_type
            ),
            AlarmConfig.objects.create(
                alarm_id="weather_summary_wind",
                view=self.summary_view,
                type=self.windspeed_type
            )
        ]
        AlarmConfig.objects.create(
            alarm_id="health_summary",
            view=self.summary_view,
            type=self.health_type
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


class RetrieveWeatherConfig(APITestBase, AlarmsConfigTestSetUp, TestCase):
    """Test suite to test a retrieve request for the weather config"""

    def setUp(self):
        """Define the test suite setup"""

        self.setTestAlarmsConfig()
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

    def test_api_can_get_weather_config(self):
        """ Test that the api can retrieve a correct json"""
        # Arrange:
        expected_data = [
            {
                'placemark': 'placemark_station_1',
                'group': 'group1',
                'station': 'station_alarm_1',
                'temperature': 'temperature_alarm_1',
                'windspeed': 'windspeed_alarm_1',
                'humidity': 'humidity_alarm_1',
            },
            {
                'placemark': 'placemark_station_2',
                'group': 'group2',
                'station': 'station_alarm_2',
                'temperature': 'temperature_alarm_2',
                'windspeed': 'windspeed_alarm_2',
                'humidity': 'humidity_alarm_2',
            },
        ]
        # Act:
        response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the information'
        )
        self.assertEqual(
            response.data,
            expected_data,
            'The information retrieved is different to the expected one'
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


class RetrieveWeatherSummary(APITestBase, AlarmsConfigTestSetUp, TestCase):
    """Test suite to test a retrieve for the weather summary"""

    def setUp(self):
        """Define the test suite setup"""

        self.setTestAlarmsConfig()
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

    def test_api_can_get_weather_summary_config(self):
        """ Test that the api can retrieve a correct json"""
        # Arrange:
        expected_data = {
            "placemark": "",
            "station": "",
            "temperature": "weather_summary_temp",
            "humidity": "weather_summary_hum",
            "windspeed": "weather_summary_wind"
        }

        # Act:
        response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the information'
        )
        self.assertEqual(
            response.data,
            expected_data,
            'The information retrieved is different to the expected one'
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


class RetrieveAntennasConfig(APITestBase, AlarmsConfigTestSetUp, TestCase):
    """Test suite to tes a retrieve request for the antennas config"""

    def setUp(self):
        """Define the test suite setup"""

        self.setTestAlarmsConfig()
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

    def test_api_can_get_antennas_config(self):
        """ Test that the api can retrieve a correct json"""
        # Arrange:
        expected_data = {
            'group_A': [
                {
                    'antenna': 'A001',
                    'placemark': 'placemark_pad_1',
                    'alarm': 'antenna_alarm_1',
                    'fire': 'antenna_alarm_1_fire',
                    'fire_malfunction': 'antenna_alarm_1_fire_malfunction',
                    'ups': 'antenna_alarm_1_ups',
                    'hvac': 'antenna_alarm_1_hvac',
                    'power': 'antenna_alarm_1_power'
                },
                {
                    'antenna': 'A002',
                    'placemark': 'placemark_pad_2',
                    'alarm': 'antenna_alarm_2',
                    'fire': '',
                    'fire_malfunction': '',
                    'ups': '',
                    'hvac': '',
                    'power': ''
                }
            ],
            'group_B': [
                {
                    'antenna': 'A003',
                    'placemark': 'placemark_pad_3',
                    'alarm': 'antenna_alarm_3',
                    'fire': '',
                    'fire_malfunction': '',
                    'ups': '',
                    'hvac': '',
                    'power': ''
                },
            ]
        }

        # Act:
        response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the information'
        )
        self.assertEqual(
            response.data,
            expected_data,
            'The information retrieved is different to the expected one'
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


class RetrieveAntennasSummaryConfig(
    APITestBase, AlarmsConfigTestSetUp, TestCase
):
    """Test suite to test a retrieve request for the antennas summary"""

    def setUp(self):
        """Define the test suite setup"""

        self.setTestAlarmsConfig()
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

    def test_api_can_get_antennas_summary_config(self):
        """ Test that the api can retrieve a correct json"""
        # Arrange:
        expected_data = "antennas_summary"

        # Act:
        response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the information'
        )
        self.assertEqual(
            response.data,
            expected_data,
            'The information retrieved is different to the expected one'
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


class RetrieveHealthSummaryConfig(
    APITestBase, AlarmsConfigTestSetUp, TestCase
):
    """Test suite to test a retrieve request for the health summary"""

    def setUp(self):
        """Define the test suite setup"""

        self.setTestAlarmsConfig()
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
        url = reverse('alarmconfig-ias-health-summary-config')
        return client.get(url, format='json')

    def test_api_can_get_ias_health_summary_config(self):
        """ Test that the api can retrieve a correct json"""
        # Arrange:
        expected_data = "health_summary"

        # Act:
        response = self.target_request_from_client(
            self.authenticated_authorized_client)
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the information'
        )
        self.assertEqual(
            response.data,
            expected_data,
            'The information retrieved is different to the expected one'
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