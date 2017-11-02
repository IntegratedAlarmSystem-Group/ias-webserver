from django.db import models
from channels.binding.websockets import WebsocketBinding
from utils.choice_enum import ChoiceEnum


class OperationalMode(ChoiceEnum):
    startup = 0
    initialization = 1
    closing = 2
    shuttedown = 3
    maintenance = 4
    operational = 5
    degraded = 6
    unknown = 7

    @classmethod
    def options(cls):
        return cls.get_choices()


class Alarm(models.Model):
    value = models.IntegerField(default=0, blank=False, null=False)
    mode = models.CharField(
        max_length=1, choices=OperationalMode.options(),
        blank=False, null=False, default=0
    )
    core_timestamp = models.PositiveIntegerField(blank=False, null=False)
    core_id = models.CharField(max_length=100)
    running_id = models.CharField(max_length=100)

    def __str__(self):
        """returns a string representation of the object"""
        return str(self.core_id) + '=' + str(self.value)


class AlarmBinding(WebsocketBinding):
    model = Alarm
    stream = "alarms"
    fields = ["value", "mode", "core_timestamp", "core_id", "running_id"]

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ["alarms_group"]

    def has_permission(self, user, action, pk):
        return True
