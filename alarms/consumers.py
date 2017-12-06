import json
from channels.generic.websockets import (
    WebsocketDemultiplexer,
    JsonWebsocketConsumer
)
from django.core import serializers
from .models import Alarm, AlarmBinding, OperationalMode


class CoreConsumer(JsonWebsocketConsumer):
    """ Consumer for messages from the core system """

    def find_alarm(self, core_id):
        alarms = Alarm.objects.filter(core_id=core_id)
        return alarms.first()

    def get_alarm_parameters(self, content):
        mode_options = dict((y, x) for x, y in OperationalMode.options())
        params = {
            'value': (1 if content['value'] == 'true' else 0),
            'core_timestamp': content['tStamp'],
            'mode': mode_options[content['mode']],
            'core_id': content['id'],
            'running_id': content['fullRunningId'],
        }
        return params

    def update_alarm(self, alarm, params):
        update = False
        setattr(alarm, 'core_timestamp', params['core_timestamp'])
        del params['core_timestamp']
        for key, value in params.items():
            if getattr(alarm, key) != value:
                setattr(alarm, key, value)
                update = True
        if update:
            alarm.save()
            return True
        return False

    def create_or_update_alarm(self, content):
        core_id = content['id']
        alarm = self.find_alarm(core_id)
        alarm_params = self.get_alarm_parameters(content)

        # New Alarm:
        if alarm is None:
            Alarm.objects.create(**alarm_params)
            return 'created'

        # Update previous Alarm:
        else:
            status = self.update_alarm(alarm, alarm_params)
            if status:
                return 'updated'
            else:
                return 'ignored'
        return 'unchanged'

    def receive(self, content, **kwargs):
        response = self.create_or_update_alarm(content)
        self.send(response)


class AlarmRequestConsumer(JsonWebsocketConsumer):

    def receive(self, content, multiplexer, **kwargs):

        if content is not None:
            if content['action'] == 'list':
                queryset = Alarm.objects.all()
                data = serializers.serialize(
                    'json',
                    list(queryset)
                )
                multiplexer.send({
                    "data": json.loads(data)
                })
            else:
                multiplexer.send({
                    "data": "Unsupported action"
                })


class AlarmDemultiplexer(WebsocketDemultiplexer):
    """Demultiplexer for Alarms notifications.

    Note:
        Check that the groups property is defined,
        since it is for real clients
    """
    consumers = {
        "alarms": AlarmBinding.consumer,
        "requests": AlarmRequestConsumer
    }

    groups = ["alarms_group"]
