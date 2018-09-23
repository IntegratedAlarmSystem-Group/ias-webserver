import json
import mock
import os
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from panels.models import File, AlarmConfig, View, Type
from panels.serializers import FileSerializer


class FileApiTestCase(TestCase):
    """Test suite for the files api views."""

    def setUp(self):
        # Arrange:
        """Define the test suite setup"""
        self.message = 'Shelved because of reasons'
        self.new_data = {
            'key': 'my_new_key',
            'url': 'my_new_url.json'
        }
        self.files = [
            File.objects.create(
                key='my_file_1',
                url='mock.json'
            ),
            File.objects.create(
                key='my_file_2',
                url='my_url_2.json'
            )
        ]
        self.old_count = File.objects.count()
        self.client = APIClient()

    # ******* CREATE
    def test_api_can_create_file(self):
        """ Test that the api can create a file """
        # Act:
        url = reverse('file-list')
        self.response = self.client.post(url, self.new_data, format='json')
        # Assert:
        created_file = File.objects.get(
            url=self.new_data['url']
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_201_CREATED,
            'The server did not create the file'
        )
        self.assertEqual(
            self.old_count + 1,
            File.objects.count(),
            'The server did not create a new file in the database'
        )
        retrieved_data = created_file.to_dict()
        self.assertEqual(
            retrieved_data,
            self.new_data,
            'The created file does not match the data sent in the request'
        )

    # ******* RETRIEVE
    def test_api_can_list_the_files(self):
        """ Test that the api can list the files """
        # Act:
        url = reverse('file-list')
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the list of files'
        )
        expected_data = [FileSerializer(t).data for t in self.files]
        self.assertEqual(
            response.data,
            expected_data,
            'The created file does not match the data sent in the request'
        )

    def test_api_can_retrieve_a_file(self):
        """ Test that the api can retrieve a file """
        # Act:
        url = reverse('file-detail', kwargs={'pk': self.files[0].pk})
        response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the file'
        )
        expected_data = FileSerializer(self.files[0]).data
        self.assertEqual(
            response.data,
            expected_data,
            'The retrieved file data does not match the file in the database'
        )

    # ******* UPDATE
    def test_api_can_update_a_file(self):
        """ Test that the api can update a file """
        # Act:
        url = reverse('file-detail', kwargs={'pk': self.files[0].pk})
        response = self.client.put(url, self.new_data, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not update the file'
        )
        retrieved_file = File.objects.get(pk=self.files[0].pk)
        self.assertEqual(
            retrieved_file.to_dict(),
            self.new_data,
            'The retrieved file data does not match the file in the database'
        )

    # ******* DELETE
    def test_api_can_delete_a_file(self):
        """ Test that the api can delete a file """
        # Act:
        url = reverse('file-detail', kwargs={'pk': self.files[0].pk})
        response = self.client.delete(url, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
            'The server did not delete the file'
        )
        self.assertEqual(
            self.old_count - 1,
            File.objects.count(),
            'The server did not delete the file in the database'
        )

    # ******* RETRIEVE FILE
    @mock.patch('panels.models.File._get_absolute_location')
    def test_api_can_get_json_from_file(self, mock):
        """ Test that the api can get a json from a .json file """
        # Arrange:
        mock_location = os.path.join(os.getcwd(), 'panels', 'tests')
        mock.return_value = mock_location
        # Act:
        url = reverse('file-get-json')
        data = {
            'key': 'my_file_1'
        }
        response = self.client.get(url, data, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the file'
        )
        file_url = self.files[0].get_full_url()
        with open(file_url) as f:
            expected_data = json.load(f)
        self.assertEqual(
            response.data,
            expected_data,
            'The retrieved file data does not match the file in the database'
        )

    def test_api_cannot_get_json_if_the_key_does_not_exist(self):
        """ Test that the api cannot get a json if the key does not exist """
        # Act:
        url = reverse('file-get-json')
        data = {
            'key': 'my_fake_key'
        }
        response = self.client.get(url, data, format='json')
        # Assert:
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            'The server did retrieve a file'
        )


class AlarmConfigApiErrorResponsesTestCase(TestCase):
    """ Test suite for the error responses in case of bad configuration """

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
            placemark="placemark_1"
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
            placemark="placemark_1",
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


class AlarmConfigApiTestCase(TestCase):
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
        self.stations_alarms_config = [
            AlarmConfig.objects.create(
                alarm_id="station_alarm_1",
                view=self.weather_view,
                type=self.station_type,
                placemark="placemark_1"
            ),
            AlarmConfig.objects.create(
                alarm_id="station_alarm_2",
                view=self.weather_view,
                type=self.station_type,
                placemark="placemark_2"
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
                placemark="placemark_1",
                custom_name="A001",
                tags="group_A"
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_2",
                view=self.antennas_view,
                type=self.antenna_type,
                placemark="placemark_2",
                custom_name="A002",
                tags="group_A"
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_3",
                view=self.antennas_view,
                type=self.antenna_type,
                placemark="placemark_3",
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
        self.client = APIClient()

    def test_api_can_get_weather_config(self):
        """ Test that the api can retrieve a correct json"""
        # Arrange:
        expected_data = [
            {
                'placemark': 'placemark_1',
                'station': 'station_alarm_1',
                'temperature': 'temperature_alarm_1',
                'windspeed': 'windspeed_alarm_1',
                'humidity': 'humidity_alarm_1',
            },
            {
                'placemark': 'placemark_2',
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
                    'placemark': 'placemark_1',
                    'alarm': 'antenna_alarm_1',
                    'fire': 'antenna_alarm_1_fire',
                    'fire_malfunction': 'antenna_alarm_1_fire_malfunction',
                    'ups': 'antenna_alarm_1_ups',
                    'hvac': 'antenna_alarm_1_hvac',
                    'power': 'antenna_alarm_1_power'
                },
                {
                    'antenna': 'A002',
                    'placemark': 'placemark_2',
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
                    'placemark': 'placemark_3',
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
