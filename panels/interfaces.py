import logging
from panels.models import AlarmConfig

logger = logging.getLogger(__name__)


class IPanels:
    """ This class defines the methods that the Panels app provides to be used
    by other apps """

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
