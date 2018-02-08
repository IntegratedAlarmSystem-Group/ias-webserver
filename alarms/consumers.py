import json
from channels.generic.websocket import (
    JsonWebsocketConsumer,
    AsyncJsonWebsocketConsumer,
)
from django.core import serializers
from .models import Alarm, OperationalMode, Validity
from alarms.collections import AlarmCollection


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
        params = {
            'value': (1 if content['value'] == 'SET' else 0),
            'core_timestamp': content['tStamp'],
            'mode': mode_options[content['mode']],
            'validity': validity_options[content['iasValidity']],
            'core_id': core_id,
            'running_id': content['fullRunningId'],
        }
        return Alarm(**params)

    async def receive_json(self, content, **kwargs):
        """
        Handles the messages received by this consumer.
        It delegates handling of the alarms received in the messages to
        :func:`~AlarmCollection.create_or_update_if_latest`

        Responds with a message indicating the action taken
        (created, updated, ignored)
        """
        if content['valueType'] == 'ALARM':
            alarm = CoreConsumer.get_alarm_from_core_msg(content)
            alarm.update_validity()
            response = AlarmCollection.create_or_update_if_latest(alarm)
        else:
            response = 'ignored-non-alarm'
        await self.send(response)


class RequestConsumer(AsyncJsonWebsocketConsumer):

    async def receive_json(self, content, **kwargs):
        """
        Handles the messages received by this consumer

        If the message contains the 'action' 'list',
        responds with the list of all the current Alarms.
        """

        if content['payload'] and content['payload']['action'] is not None:
            if content['payload']['action'] == 'list':
                queryset = AlarmCollection.update_all_alarms_validity()
                data = serializers.serialize(
                    'json',
                    list(queryset.values())
                )
                await self.send_json({
                    "payload": {
                        "data": json.loads(data)
                    }
                })
            else:
                await self.send_json({
                    "payload": {
                        "data": "Unsupported action"
                    }
                })


class NotifyConsumer(AsyncJsonWebsocketConsumer):

    async def notify(self, alarm, **kwargs):
        """
        Notifies the client of changes in an Alarm
        """

        if alarm is not None:
            data = serializers.serialize(
                'json',
                alarm
            )
            await self.send_json({
                "payload": {
                    "data": json.loads(data)
                }
            })
        else:
            await self.send_json({
                    "payload": {
                        "data": "Null Alarm"
                    }
                })
