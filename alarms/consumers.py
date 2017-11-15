# from django.http import HttpResponse
# from channels.handler import AsgiHandler
from channels.generic.websockets import (
    WebsocketDemultiplexer,
    JsonWebsocketConsumer
)
from django.core import serializers
from .models import Alarm, AlarmBinding


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
                    "text": data
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
