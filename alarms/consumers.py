# from django.http import HttpResponse
# from channels.handler import AsgiHandler
from channels.generic.websockets import WebsocketDemultiplexer
from .models import AlarmBinding


class AlarmDemultiplexer(WebsocketDemultiplexer):
    consumers = {
        "alarms": AlarmBinding.consumer,
    }

    groups = ["alarms_group"]
