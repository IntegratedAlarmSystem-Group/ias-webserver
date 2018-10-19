from panels.models import AlarmConfig, Placemark


class IPanels:
    """ This class defines the methods that the Panels app provides to be used
    by other apps """

    @classmethod
    def update_antennas_configuration(self, antennas_pads_association):
        """
        Updates the antennas pad association in the panels configuration

        Args:
            antennas_pads_association (String): Association between
            antennas and pads got from ias core value Array-AntennasToPads
            The string must have the following form:
            ANTENNA1:PAD_A,ANTENNA2:PAD_B,..,ANTENNA_N:PAD_X
        """
        # Parse antennas pads association
        associations = {}
        for item in antennas_pads_association.split(','):
            antenna_pad = item.split(':')  # ANTENNA:PAD
            associations[antenna_pad[0]] = antenna_pad[1]

        antennas_configuration = AlarmConfig.objects.filter(
                                    view__name="antennas",
                                    type__name="antenna"
                                )
        for config in antennas_configuration:
            placemark_name = associations[config.custom_name]
            config.placemark = Placemark.objects.filter(
                name=placemark_name).first()
            config.save()

    @classmethod
    def get_alarm_ids_of_alarm_configs(self):
        """
        Returns a list with the ids (alarm_id) of all the AlarmConfigs

        Returns:
            (list): the list of alarm ids
        """
        configs = AlarmConfig.objects.all()
        ids = [config.alarm_id for config in configs]
        return ids
