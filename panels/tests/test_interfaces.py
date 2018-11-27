from panels.interfaces import IPanels
from django.test import TestCase
from panels.models import (
    AlarmConfig,
    View,
    Type,
    Placemark,
    PlacemarkType
)


class TestIPanels(TestCase):
    """This class defines the test suite for the Panels Interfaces"""

    def setUp(self):
        # Arrange:
        """Define the test suite setup"""

        self.antenna_pad_association = "A000:PAD0,A001:PAD1,A002:PAD2"
        self.antennas_view = View.objects.create(name='antennas')
        self.antenna_type = Type.objects.create(name='antenna')
        self.alarm_config_items = [
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_0",
                view=self.antennas_view,
                type=self.antenna_type,
                custom_name="A000",
                tags="group_A"
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_1",
                view=self.antennas_view,
                type=self.antenna_type,
                custom_name="A001",
                tags="group_A"
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_2",
                view=self.antennas_view,
                type=self.antenna_type,
                custom_name="A002",
                tags="group_A"
            )
        ]
        self.placemark_type = PlacemarkType.objects.create(name='pad')
        self.placemarks = [
            Placemark.objects.create(
                name="PAD0",
                type=self.placemark_type
            ),
            Placemark.objects.create(
                name="PAD1",
                type=self.placemark_type
            ),
            Placemark.objects.create(
                name="PAD2",
                type=self.placemark_type
            )
        ]

    def test_update_antennas_configuration(self):
        """
        Test that IPanels.update_antennas_configuration update the values
        """
        # Arrange:
        antennas_config = AlarmConfig.objects.filter(
                            view__name="antennas",
                            type__name="antenna"
                          )
        for item in antennas_config:
            self.assertTrue(
                item.placemark is None,
                "The antennas have placemarks associated before the update")
        # Act:
        IPanels.update_antennas_configuration(self.antenna_pad_association)
        # Assert:
        antennas_config = AlarmConfig.objects.filter(
                            view__name="antennas",
                            type__name="antenna"
                          )
        for i, item in enumerate(antennas_config):
            self.assertTrue(
                item.placemark.name == "PAD{}".format(i),
                "The antennas have not been updated as expected")

    def test_get_alarm_ids_of_alarm_configs(self):
        """
        Test that IPanels.get_alarm_ids_of_alarm_configs returns the alarm_ids
        """
        # Arrange:
        antennas_config = AlarmConfig.objects.filter(
                            view__name="antennas",
                            type__name="antenna"
                          )
        for item in antennas_config:
            self.assertTrue(
                item.placemark is None,
                "The antennas have placemarks associated before the update")
        # Act:
        ids = IPanels.get_alarm_ids_of_alarm_configs()
        # Assert:
        self.assertEqual(
            ids,
            ["antenna_alarm_0", "antenna_alarm_1", "antenna_alarm_2"]
        )

    def test_get_alarms_views_dict_of_alarm_configs(self):
        """
        Test that IPanels.get_alarms_views_dict_of_alarm_configs
        returns the related views
        """

        expected = {
            "antenna_alarm_0": ["antennas"],
            "antenna_alarm_1": ["antennas"],
            "antenna_alarm_2": ["antennas"],
        }

        # Act:
        response = IPanels.get_alarms_views_dict_of_alarm_configs()

        # Assert:
        self.assertDictEqual(response, expected)

    def test_get_names_of_views(self):
        """
        Test that IPanels.get_names_of_views
        returns a list with the views names
        """

        expected = ["antennas"]

        # Act:
        response = IPanels.get_names_of_views()

        # Assert:
        self.assertEqual(expected, response)
