from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from panels.models import (
    AlarmConfig,
    View,
    Type,
    Placemark,
    PlacemarkType
)


class AlarmConfigApiErrorResponsesTestCase(TestCase):
    """ Test suite for the error responses in case of bad configuration """

    def setUp(self):
        """ Define the test suite setup """
        self.placemark_type = PlacemarkType.objects.create(name='pad')
        self.placemark = Placemark.objects.create(
            name="placemark_1",
            type=self.placemark_type
        )

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
