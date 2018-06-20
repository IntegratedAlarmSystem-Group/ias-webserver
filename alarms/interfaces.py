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
            alarms_id (list): List of IDs of the Alarms to acknowledge
        """
        async_to_sync(AlarmCollection.acknowledge)(alarm_ids)

    @classmethod
    def shelve_alarm(self, alarm_id):
        """
        Shelve an Alarm based on an Alarm ID

        Args:
            alarm_id (string): ID of the Alarms to shelve
        """
        async_to_sync(AlarmCollection.shelve)(alarm_id)

    @classmethod
    def unshelve_alarm(self, alarm_id):
        """
        Unshelve an Alarm based on an Alarm ID

        Args:
            alarm_id (string): ID of the Alarms to unshelve
        """
        async_to_sync(AlarmCollection.unshelve)(alarm_id)
