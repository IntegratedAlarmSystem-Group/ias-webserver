from asgiref.sync import async_to_sync
from alarms.collections import AlarmCollection


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
        """
        async_to_sync(AlarmCollection.acknowledge)(alarm_ids)
