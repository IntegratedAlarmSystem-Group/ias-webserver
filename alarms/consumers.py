import time
import datetime
import re
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from alarms.models import Alarm, OperationalMode, Validity, Value, IASValue
from alarms.collections import AlarmCollection, AlarmCollectionObserver

logger = logging.getLogger(__name__)


class CoreConsumer(AsyncJsonWebsocketConsumer):
    """ Consumer for messages from the core system """

    pattern = re.compile('\\[!#\\d+!\\]')
    num_pattern = re.compile('\d+')

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
        # Extract the core_id
        core_id = full_id.rsplit('@', 1)[1].strip('()').split(':')[0]

        # If it matches the pattern, it is edited accordingly
        match = CoreConsumer.pattern.search(core_id)
        if match:
            core_id_start = core_id[0:match.start()]
            matched = match.group()
            num_matched = CoreConsumer.num_pattern.search(matched).group()
            core_id = core_id_start + ' instance ' + num_matched

        return core_id

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
            dependencies = []
            for dependency in list(content['depsFullRunningIds']):
                dependencies.append(CoreConsumer.get_core_id_from(dependency))
            return dependencies
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
        value_options = Value.get_choices_by_name()
        mode_options = OperationalMode.get_choices_by_name()
        validity_options = Validity.get_choices_by_name()
        core_id = CoreConsumer.get_core_id_from(content['fullRunningId'])
        core_timestamp = CoreConsumer.get_timestamp_from(
            content['sentToBsdbTStamp'])
        params = {
            'value': value_options[content['value']],
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

    def get_value_from_core_msg(content):
        """
        Returns an IASValue based on the message content

        Args:
            content (dict): the content of the messsage

        Returns:
            IASValue: an Object based on the message content
        """
        mode_options = OperationalMode.get_choices_by_name()
        validity_options = Validity.get_choices_by_name()
        core_id = CoreConsumer.get_core_id_from(content['fullRunningId'])
        core_timestamp = CoreConsumer.get_timestamp_from(
            content['sentToBsdbTStamp'])
        params = {
            'value': content['value'],
            'core_timestamp': core_timestamp,
            'mode': mode_options[content['mode']],
            'validity': validity_options[content['iasValidity']],
            'core_id': core_id,
            'running_id': content['fullRunningId'],
            'timestamps': CoreConsumer.get_timestamps(content)
        }
        return IASValue(**params)

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
            logger.debug(
                'new alarm received by the consumer: %s',
                alarm.to_dict())
        else:
            value = CoreConsumer.get_value_from_core_msg(content)
            value.update_validity()
            status = AlarmCollection.add_or_update_value(value)
            response = status
            logger.debug(
                'new ias value received by the consumer: %s',
                value.to_dict())
        await self.send(response)


class ClientConsumer(AsyncJsonWebsocketConsumer, AlarmCollectionObserver):
    """ Consumer to notify clients and listen their requests """
    groups = []

    async def connect(self):
        """
        Called on connection
        """
        if self.scope['user'].is_anonymous:
            # To reject the connection:
            await self.close()
        else:
            AlarmCollection.register_observer(self)
            # To accept the connection call:
            await self.accept()

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
                    logger.debug(
                        'new message received in requests stream: ' +
                        '(action list)')
                else:
                    await self.send_json({
                        "payload": {
                            "data": "Unsupported action"
                        },
                        "stream": "requests",
                    })
                    logger.debug(
                        'new message received in requests stream: ' +
                        '(unsupported action)')
        if content['stream'] == 'broadcast':
            await AlarmCollection.broadcast_status_to_observers()
            logger.debug('new message received in broadcast stream')

    async def disconnect(self, close_code):
        """
        Called when the socket closes
        """
        if self in AlarmCollection.observers:
            AlarmCollection.observers.remove(self)
