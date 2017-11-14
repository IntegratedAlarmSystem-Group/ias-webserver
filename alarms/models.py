from django.db import models
from channels.binding.websockets import WebsocketBinding
from utils.choice_enum import ChoiceEnum

# Always keep models and bindings in this file!!


class OperationalMode(ChoiceEnum):
    """ Operational Mode of a monitor point value. """

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
        """ Return a list of tuples with the valid options. """
        return cls.get_choices()


class Alarm(models.Model):
    """ Alarm generated by some device in the observatory. """


    value = models.IntegerField(default=0, blank=False, null=False)
    """ Integer that indicates the alarm. Can be either 0 (CLEARED) or 1 (SET or raised). """

    mode = models.CharField(
        max_length=1, choices=OperationalMode.options(),
        blank=False, null=False, default=0
    )
    """ Operational Mode of a monitor point value. """

    core_timestamp = models.PositiveIntegerField(blank=False, null=False)
    """ Timestamp inherited from IAS core processing. It correspond to the time when the 
    value has been read from the remote system. 
    """

    core_id = models.CharField(max_length=100)
    """ Id used to identify the Alarm in the IAS Core. """

    running_id = models.CharField(max_length=100)
    """ Id used to identify the Alarm and its parents in the IAS Core. """

    def __str__(self):
        """ Returns a string representation of the object """
        return str(self.core_id) + '=' + str(self.value)


class AlarmBinding(WebsocketBinding):
    """ Bind the alarm actions with a websocket stream. """

    model = Alarm
    """ Model binded with the websocket """

    stream = "alarms"
    """ Name of the stream to send the messages. """

    fields = "__all__"
    """ List of fields included in the messages. """

    @classmethod
    def group_names(cls, *args, **kwargs):
        """ Return a list of the groups that receive the binding messages. """
        
        return ["alarms_group"]

    def has_permission(self, user, action, pk):
        """ Return if the user has permission to make the specified action. """
        
        return True
