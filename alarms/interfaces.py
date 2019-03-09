from asgiref.sync import async_to_sync
from alarms.collections import AlarmCollection


class IAlarms:
    """ This class defines the methods that the Alarms app provides to be used
    by other apps """

    @classmethod
    def acknowledge_alarms(self, alarm_ids):
        """
        Akcnowledge Alarms based on a list of Alarm IDs

        Args:
            alarms_ids (list): List of IDs of the Alarms to acknowledge
        """
        return async_to_sync(AlarmCollection.acknowledge)(alarm_ids)

    @classmethod
    def shelve_alarm(self, alarm_id):
        """
        Shelve an Alarm based on an Alarm ID

        Args:
            alarm_id (string): ID of the Alarms to shelve
        """
        return async_to_sync(AlarmCollection.shelve)(alarm_id)

    @classmethod
    def unshelve_alarms(self, alarm_ids):
        """
        Unshelve Alarms based on a list of Alarm IDs

        Args:
            alarms_ids (list): List of IDs of the Alarms to unshelve
        """
        return async_to_sync(AlarmCollection.unshelve)(alarm_ids)

    @classmethod
    def get_alarm_dependencies(self, alarm_id):
        """
        Get the dependencies of the specified alarm

        Args:
            alarm_id (string): The id of the alarm to get the dependencies
        """
        return AlarmCollection.get_dependencies_recursively(alarm_id)

    @classmethod
    def get_alarm_ancestors(self, alarm_id):
        """
        Get the ancestors of the specified alarm

        Args:
        alarm_id (string): The id of the alarm to get the ancestors
        """
        return AlarmCollection.get_ancestors_recursively(alarm_id)

    @classmethod
    def get_value(self, value_id):
        """
        Get a selected IASValue from the values_collection

        Args:
        value_id (string): The core_id of the value
        """
        return AlarmCollection.get_value(value_id)
