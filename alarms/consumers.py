import time
import datetime
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from alarms.models import Alarm, OperationalMode, Validity
from alarms.collections import AlarmCollection, AlarmCollectionObserver


class CoreConsumer(AsyncJsonWebsocketConsumer):
    """ Consumer for messages from the core system """

    def get_core_id_from(full_id):
        """Return the core_id value extracted from the full running id field
        assuming an specific format.

        Args:
            full_id (string): The fullRunningId value provided by the core
            following the format of the example below
            example: '(A_value:A_type)@(B_value:B_type)@(C_value:C_type)'

        Returns:
            string: The core id value. According to the previous example, the
            value would be C_value
        """
        return full_id.rsplit('@', 1)[1].strip('()').split(':')[0]

    def get_timestamp_from(bsdbTStamp):
        """Return the bsdbTStamp transformed to timestamp in milliseconds

        Args:
            bsdbTStamp (string): The backstage timestamp in ISO 8601 format

        Returns:
            double: The backstage timestamp in milliseconds
        """
        dt = datetime.datetime.strptime(bsdbTStamp, '%Y-%m-%dT%H:%M:%S.%f')
        timestamp = (time.mktime(dt.timetuple()) + dt.microsecond / 1E6) * 1000
        return int(timestamp)

    def get_timestamps(content):
        """ Return a dictionary with all the available timestamps in the content
        """
        timestamps = {}
        for field in content.keys():
            if field.endswith('TStamp'):
                timestamps[field] = CoreConsumer.get_timestamp_from(
                    content[field])
        return timestamps

    def get_dependencies(content):
        """ Return a list with the dependencies of the alarm"""
        if 'depsFullRunningIds' in content.keys():
            return list(content['depsFullRunningIds'])
        else:
            return []

    def get_properties(content):
        """ Return a dictionary with the properties of the alarm"""
        props = content['props'] if 'props' in content.keys() else {}
        return props

    def get_alarm_from_core_msg(content):
        """
        Returns an alarm based on the values specified in the message content

        Args:
            content (dict): the content of the messsage

        Returns:
            Alarm: an alarm based on the message content
        """
        mode_options = OperationalMode.get_choices_by_name()
        validity_options = Validity.get_choices_by_name()
        core_id = CoreConsumer.get_core_id_from(content['fullRunningId'])
        core_timestamp = CoreConsumer.get_timestamp_from(
            content['sentToBsdbTStamp'])
        params = {
            'value': (1 if content['value'] == 'SET' else 0),
            'core_timestamp': core_timestamp,
            'mode': mode_options[content['mode']],
            'validity': validity_options[content['iasValidity']],
            'core_id': core_id,
            'running_id': content['fullRunningId'],
            'timestamps': CoreConsumer.get_timestamps(content),
            'properties': CoreConsumer.get_properties(content),
            'dependencies': CoreConsumer.get_dependencies(content)
        }
        return Alarm(**params)

    async def receive_json(self, content, **kwargs):
        """
        Handles the messages received by this consumer.
        It delegates handling of the alarms received in the messages to
        :func:`~AlarmCollection.add_or_update_and_notify`

        Responds with a message indicating the action taken
        (created, updated, ignored)
        """
        if content['valueType'] == 'ALARM':
            alarm = CoreConsumer.get_alarm_from_core_msg(content)
            alarm.update_validity()
            response = await AlarmCollection.add_or_update_and_notify(alarm)
        else:
            response = 'ignored-non-alarm'
        await self.send(response)


class ClientConsumer(AsyncJsonWebsocketConsumer, AlarmCollectionObserver):
    """ Consumer to notify clients and listen their requests """

    def __init__(self, scope):
        """
        Initializes the consumer and subscribes it to the AlarmCollection
        observers list
        """
        super()
        AlarmCollection.register_observer(self)

    async def update(self, alarm, action):
        """
        Notifies the client of changes in an Alarm
        """
        message = None
        if alarm is not None:
            message = {
                "payload": {
                    "data": alarm.to_dict(),
                    "action": action
                },
                "stream": "alarms",
            }
        else:
            message = {
                "payload": {
                    "data": "Null Alarm",
                    "action": action
                },
                "stream": "alarms",
            }
        await self.send_json(message)

    async def send_alarms_status(self):
        queryset = AlarmCollection.update_all_alarms_validity()
        data = []
        for item in list(queryset.values()):
            data.append(item.to_dict())
        await self.send_json({
            "payload": {
                "data": data
            },
            "stream": "requests",
        })

    async def receive_json(self, content, **kwargs):
        """
        Handles the messages received by this consumer

        If the message contains the 'action' 'list',
        responds with the list of all the current Alarms.
        """
        if content['stream'] == 'requests':
            if content['payload'] and content['payload']['action'] is not None:
                if content['payload']['action'] == 'list':
                    await self.send_alarms_status()
                else:
                    await self.send_json({
                        "payload": {
                            "data": "Unsupported action"
                        },
                        "stream": "requests",
                    })
        if content['stream'] == 'broadcast':
            await AlarmCollection.broadcast_status_to_observers()
