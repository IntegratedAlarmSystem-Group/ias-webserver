# from django.http import HttpResponse
# from channels.handler import AsgiHandler
from channels.generic.websockets import WebsocketDemultiplexer
from .bindings import AlarmBinding


class AlarmDemultiplexer(WebsocketDemultiplexer):
    consumers = {
        "alarms": AlarmBinding.consumer,
    }

    groups = ["binding.values"]
