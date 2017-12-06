import json
from channels.generic.websockets import (
    WebsocketDemultiplexer,
    JsonWebsocketConsumer
)
from django.core import serializers
from .models import Alarm, AlarmBinding


class CoreConsumer(JsonWebsocketConsumer):
    """ Consumer for messages from the core system """

    def receive(self, content, **kwargs):
        self.send(content)   # send echo


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
