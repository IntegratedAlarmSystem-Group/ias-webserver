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


class AlarmConfigApiTestCase(APITestBase, TestCase):
    """Test suite for the AlarmConfig api views."""

    def setUp(self):
        # Arrange:
        """Define the test suite setup"""
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

        self.old_count = AlarmConfig.objects.count()
        self.no_permissions_user = self.create_user(
            username='user', password='123', permissions=[])
        self.authenticated_client = APIClient()
        self.authenticate_client_using_token(
            self.authenticated_client,
            Token.objects.get(user__username=self.no_permissions_user)
        )
        self.client = self.authenticated_client

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
        url = reverse('alarmconfig-weather-config')
        response = self.client.get(url, format='json')
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
        url = reverse('alarmconfig-antennas-config')
        response = self.client.get(url, format='json')
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

    def test_api_can_get_antennas_summary_config(self):
        """ Test that the api can retrieve a correct json"""
        # Arrange:
        expected_data = "antennas_summary"

        # Act:
        url = reverse('alarmconfig-antennas-summary-config')
        response = self.client.get(url, format='json')
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
        url = reverse('alarmconfig-weather-summary-config')
        response = self.client.get(url, format='json')
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
