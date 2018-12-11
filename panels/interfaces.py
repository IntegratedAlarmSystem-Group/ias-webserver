import logging
from panels.models import AlarmConfig, Placemark, View

logger = logging.getLogger(__name__)


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
        if not antennas_configuration:
            logger.warning(
                'there is no configuration for antenna alarm type ' +
                'in the antennas view')

        for config in antennas_configuration:
            placemark_name = associations[config.custom_name]
            config.placemark = Placemark.objects.filter(
                name=placemark_name).first()
            config.save()
        logger.debug(
            '%d antennas configuration were updated',
            len(antennas_configuration))

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

    @classmethod
    def get_alarms_views_dict_of_alarm_configs(self):
        """
        Returns a dict with the names of the views
        related to an alarm from all the AlarmConfigs

        Returns:
            (dict): dictionary of views names with alarm_ids as keys
        """
        q = AlarmConfig.objects.all()
        return {config.alarm_id: [config.view.name] for config in q}

    @classmethod
    def get_names_of_views(self):
        """
        Returns a list with the names of the views

        Returns:
            (list): the list of names of the views
        """
        views = View.objects.all()
        names = [view.name for view in views]
        return names
