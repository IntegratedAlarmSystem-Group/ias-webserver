from channels.binding.websockets import WebsocketBinding
from .models import Alarm


class AlarmBinding(WebsocketBinding):

    model = Alarm
    stream = "alarms"
    fields = ["value", "mode", "core_timestamp", "core_id", "running_id"]

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["binding.alarms"]

    def has_permission(self, user, action, pk):
        return True
