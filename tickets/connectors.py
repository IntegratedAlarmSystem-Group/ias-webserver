from alarms.interfaces import IAlarms


class AlarmConnector:
    """
    This class defines methods to communicate the Ticket app with the Alarm app
    """

    @classmethod
    def acknowledge_alarms(self, alarm_ids):
        """
        Akcnowledge Alarms based on a list of Alarm IDs

        Args:
            alarms_id (list): List of IDs of the Alarms to acknowledge
        Return:
            List of IDs of the acknowledged alarms
        """
        return IAlarms.acknowledge_alarms(alarm_ids)

    @classmethod
    def shelve_alarm(self, alarm_id):
        """
        Shelve an Alarm based on an Alarm ID

        Args:
            alarm_id (string): ID of the Alarms to shelve
        """
        IAlarms.shelve_alarm(alarm_id)

    @classmethod
    def unshelve_alarms(self, alarm_ids):
        """
        Unshelve Alarms based on a list of Alarm IDs

        Args:
            alarms_id (list): List of IDs of the Alarms to unshelve
        """
        IAlarms.unshelve_alarms(alarm_ids)

    @classmethod
    def get_alarm_dependencies(self, alarm_id):
        """
        Get the dependencies of the specified alarm

        Args:
        alarm_id (string): The id of the alarm to get the dependencies
        """
        return IAlarms.get_alarm_dependencies(alarm_id)

    @classmethod
    def get_alarm_ancestors(self, alarm_id):
        """
        Get the ancestors of the specified alarm

        Args:
        alarm_id (string): The id of the alarm to get the ancestors
        """
        return IAlarms.get_alarm_ancestors(alarm_id)
