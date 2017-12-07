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
        """
        Finds the alarm, searching by its core_id

        Args:
            core_id (string): the core_id of the alarm

        Returns:
            Alarm: the Alarm object stored in the Database
        """
        alarms = Alarm.objects.filter(core_id=core_id)
        return alarms.first()

    def get_alarm_parameters(self, content):
        """
        Returns the parameters of the alarm as a dict indexed by
        attribute names (the names in the Alarm class)

        Args:
            content (dict): the content of the messsage

        Returns:
            dict: a dict of the form {attribute: value}
        """
        mode_options = OperationalMode.get_choices_by_name()
        params = {
            'value': (1 if content['value'] == 'true' else 0),
            'core_timestamp': content['tStamp'],
            'mode': mode_options[content['mode']],
            'core_id': content['id'],
            'running_id': content['fullRunningId'],
        }
        return params

    def update_alarm(self, alarm, params):
        """
        Updates the alarm with the values given in a dict,
        according to some conditions.

        Args:
            alarm (Alarm): The alarm object to update.
            params (dict): Dictionary of values indexed by parameter names

        Returns:
            bool: True if the alarm was updated, False if not
        """
        # Update core_timestamp:
        setattr(alarm, 'core_timestamp', params['core_timestamp'])

        # Update the rest of the attributes only if they are different:
        update = False
        del params['core_timestamp']
        for key, value in params.items():
            if getattr(alarm, key) != value:
                setattr(alarm, key, value)
                update = True

        # Save changes only if there was a different attribute (except core_id)
        if update:
            alarm.save()
            return True
        return False

    def create_or_update_alarm(self, content):
        """
        Creates or updates the alarm received from the message according to
        defined criteria
        """
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
        """
        Handles the messages received by this consumer.
        Delegates handling of the alamrs received in the messages to
        :func:`~create_or_update_alarm`

        Responds with a message indicating the action taken
        (create, update, ignore)
        """
        response = self.create_or_update_alarm(content)
        self.send(response)


class AlarmRequestConsumer(JsonWebsocketConsumer):

    def receive(self, content, multiplexer, **kwargs):
        """
        Handles the messages received by this consumer

        If the message contains the 'action' 'list',
        responds with the list of all the current Alarms.
        """

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
