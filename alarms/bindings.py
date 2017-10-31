from channels.binding.websockets import WebsocketBinding
from .models import Alarm


class AlarmBinding(WebsocketBinding):

    model = Alarm
    stream = "stream.alarms"
    fields = ["core_id", "value"]

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["binding.alarms"]

    def has_permission(self, user, action, pk):
        return True
