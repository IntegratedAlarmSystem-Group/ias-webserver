# from django.http import HttpResponse
# from channels.handler import AsgiHandler
from channels.generic.websockets import WebsocketDemultiplexer
from .models import AlarmBinding


class AlarmDemultiplexer(WebsocketDemultiplexer):
    """Demultiplexer for Alarms.

    Note:
        Check that the groups property is defined,
        since it is for real clients
    """
    consumers = {
        "alarms": AlarmBinding.consumer,
    }

    groups = ["alarms_group"]
