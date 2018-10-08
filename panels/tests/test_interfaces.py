from panels.interfaces import IPanels
from django.test import TestCase
from panels.models import AlarmConfig, View, Type

class TestIPanels(TestCase):
    """This class defines the test suite for the Panels Interfaces"""

    def setUp(self):
        # Arrange:
        """Define the test suite setup"""

        self.antenna_pad_association = "A000:PAD0,A001:PAD1,A002:PAD2,A003:PAD3"
        self.antennas_view = View.objects.create(name='antennas')
        self.antenna_type = Type.objects.create(name='antenna')
        self.alarm_config_items = [
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_0",
                view=self.antennas_view,
                type=self.antenna_type,
                placemark="",
                custom_name="A000",
                tags="group_A"
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_1",
                view=self.antennas_view,
                type=self.antenna_type,
                placemark="",
                custom_name="A001",
                tags="group_A"
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_2",
                view=self.antennas_view,
                type=self.antenna_type,
                placemark="",
                custom_name="A002",
                tags="group_A"
            ),
            AlarmConfig.objects.create(
                alarm_id="antenna_alarm_3",
                view=self.antennas_view,
                type=self.antenna_type,
                placemark="",
                custom_name="A003",
                tags="group_A"
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
            self.assertTrue(item.placemark == "",
                "The antennas have placemarks associated before the update")
        # Act:
        IPanels.update_antennas_configuration(self.antenna_pad_association)
        # Assert:
        antennas_config = AlarmConfig.objects.filter(
                            view__name="antennas",
                            type__name="antenna"
                          )
        for i, item in enumerate(antennas_config):
            self.assertTrue(item.placemark == "PAD{}".format(i),
                "The antennas have not been updated as expected")
