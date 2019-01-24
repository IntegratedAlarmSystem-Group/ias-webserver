import mock
from panels.interfaces import IPanels
from django.test import TestCase
from panels.models import AlarmConfig


class TestIPanels(TestCase):
    """This class defines the test suite for the Panels Interfaces"""

    def setUp(self):
        # Arrange:
        """Define the test suite setup"""

        alarm_configurations = [
            {
                "alarm_id": "antenna_alarm_0",
                "custom_name": "A000",
                "type": "antenna",
                "view": "antennas",
                "placemark": "A000",
                "group": "",
                "children": []
            },
            {
                "alarm_id": "antenna_alarm_1",
                "custom_name": "A001",
                "type": "antenna",
                "view": "antennas",
                "placemark": "A001",
                "group": "",
                "children": []
            },
            {
                "alarm_id": "antenna_alarm_2",
                "custom_name": "A002",
                "type": "antenna",
                "view": "antennas",
                "placemark": "A002",
                "group": "",
                "children": []
            },
            {
                "alarm_id": "weather_alarm_0",
                "custom_name": "",
                "type": "windspeed",
                "view": "weather",
                "placemark": "",
                "group": "S",
                "children": []

            }
        ]

        self.alarm_configurations = [
            AlarmConfig(e) for e in alarm_configurations
        ]

    @mock.patch(
        'panels.models.AlarmConfig.objects.all')
    def test_get_alarm_ids_of_alarm_configs(
        self, mock_all_alarm_configs
    ):
        """
        Test that IPanels.get_alarm_ids_of_alarm_configs returns the alarm_ids
        """
        # Arrange:
        mock_all_alarm_configs.return_value = self.alarm_configurations
        expected_ids = [
            "antenna_alarm_0",
            "antenna_alarm_1",
            "antenna_alarm_2",
            "weather_alarm_0"
        ]

        # Act:
        ids = IPanels.get_alarm_ids_of_alarm_configs()

        # Assert:
        self.assertEqual(
            sorted(ids),
            sorted(expected_ids)
        )

    @mock.patch(
        'panels.models.AlarmConfig.objects.all')
    def test_get_alarms_views_dict_of_alarm_configs(
        self, mock_all_alarm_configs
    ):
        """
        Test that IPanels.get_alarms_views_dict_of_alarm_configs
        returns the related views
        """
        # Arrange:
        mock_all_alarm_configs.return_value = self.alarm_configurations

        expected = {
            "antenna_alarm_0": ["antennas"],
            "antenna_alarm_1": ["antennas"],
            "antenna_alarm_2": ["antennas"],
            "weather_alarm_0": ["weather"]
        }

        # Act:
        response = IPanels.get_alarms_views_dict_of_alarm_configs()

        # Assert:
        self.assertDictEqual(response, expected)
