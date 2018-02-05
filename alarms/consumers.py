import json
from channels.generic.websockets import (
    WebsocketDemultiplexer,
    JsonWebsocketConsumer
)
from django.core import serializers
from django.db import transaction
from .models import Alarm, AlarmBinding, OperationalMode, Validity
from cdb.models import Iasio
import time


class CoreConsumer(JsonWebsocketConsumer):
    """ Consumer for messages from the core system """

    __Alarms = {}
    # Add all the alarms saved in the database when the app starts
    for alarm in Alarm.objects.all():
        __Alarms[alarm.core_id] = alarm.__dict__

    def get_core_id_from(full_id):
        """Return the core_id value extracted from the full running id field
        assuming an specific format.

        Args:
            full_id (string): The fullRunningId value provided by the core
            following the format of the example below
            example: '(A_value:A_type)@(B_value:B_type)@(C_value:C_type)'

        Returns:
            string: The core id value. According to the previous example, the
            value would be C_value
        """
        return full_id.rsplit('@', 1)[1].strip('()').split(':')[0]

    def get_alarm_parameters(content):
        """
        Returns the parameters of the alarm as a dict indexed by
        attribute names (the names in the Alarm class)

        Args:
            content (dict): the content of the messsage

        Returns:
            dict: a dict of the form {attribute: value}
        """
        mode_options = OperationalMode.get_choices_by_name()
        validity_options = Validity.get_choices_by_name()
        core_id = CoreConsumer.get_core_id_from(content['fullRunningId'])
        params = {
            'value': (1 if content['value'] == 'SET' else 0),
            'core_timestamp': content['tStamp'],
            'mode': mode_options[content['mode']],
            'validity': validity_options[content['iasValidity']],
            'core_id': core_id,
            'running_id': content['fullRunningId'],
        }
        return params

    def create_or_update_alarm(alarm_params):
        """
        Creates or updates the alarm according to defined criteria
        """
        try:
            alarm = Alarm.objects.get(core_id=alarm_params['core_id'])
            is_different = alarm.check_changes(alarm_params)

            status = False
            if is_different:
                with transaction.atomic():
                    alarm = Alarm.objects.get(core_id=alarm_params['core_id'])
                    status = alarm.update_ignoring_timestamp(alarm_params)
            if status:
                return 'updated'
            else:
                return 'ignored'
        except Alarm.DoesNotExist:
            alarm = Alarm.objects.create(**alarm_params)
            return 'created'

    def calc_validity(alarm_params):
        """
        Calculate the validity considering the current time and the refresh
        rate plus a previously defined delta time
        """
        # TODO: add refresh rate to the message received if possible
        if alarm_params['validity'] == 'UNRELIABLE':
            return '0'
        iasio = Iasio.objects.get(io_id=alarm_params['core_id'])
        refresh_rate = iasio.refresh_rate
        current_timestamp = int(round(time.time() * 1000))
        alarm_timestamp = alarm_params['core_timestamp']
        delta = Validity.delta()
        validity = alarm_params['validity']

        if current_timestamp - alarm_timestamp > refresh_rate + delta:
            validity = '0'
        else:
            validity = '1'
        return validity

    def receive(self, content, **kwargs):
        """
        Handles the messages received by this consumer.
        Delegates handling of the alamrs received in the messages to
        :func:`~create_or_update_alarm`

        Responds with a message indicating the action taken
        (created, updated, ignored)
        """
        if content['valueType'] == 'ALARM':
            alarm_params = CoreConsumer.get_alarm_parameters(content)
            received_timestamp = alarm_params['core_timestamp']
            if alarm_params['core_id'] not in CoreConsumer.get_alarms().keys():
                CoreConsumer.add_alarm(alarm_params)
                response = CoreConsumer.create_or_update_alarm(alarm_params)
            stored_alarm = CoreConsumer.get_alarm(alarm_params['core_id'])
            stored_timestamp = stored_alarm['core_timestamp']
            if received_timestamp >= stored_timestamp:
                updated_validity = CoreConsumer.calc_validity(alarm_params)
                alarm_params['validity'] = updated_validity
                response = CoreConsumer.create_or_update_alarm(alarm_params)
                CoreConsumer.add_alarm(alarm_params)
            else:
                response = 'ignored-old-alarm'
        else:
            response = 'ignored-non-alarm'
        self.send(response)

    @staticmethod
    def get_alarms():
        return CoreConsumer.__Alarms

    @staticmethod
    def add_alarm(alarm_params):
        CoreConsumer.__Alarms[alarm_params['core_id']] = alarm_params.copy()

    @staticmethod
    def get_alarm(core_id):
        return CoreConsumer.__Alarms[core_id].copy()

    @staticmethod
    def delete_alarms():
        CoreConsumer.__Alarms = {}

    @staticmethod
    def update_all_alarms_validity():
        for core_id in CoreConsumer.__Alarms.keys():
            alarm_params = CoreConsumer.__Alarms[core_id]
            original_validity = alarm_params['validity']
            updated_validity = CoreConsumer.calc_validity(alarm_params)
            if original_validity != updated_validity:
                CoreConsumer.add_alarm(alarm_params)
                alarm_params['validity'] = updated_validity
                CoreConsumer.create_or_update_alarm(alarm_params)


class AlarmRequestConsumer(JsonWebsocketConsumer):

    def receive(self, content, multiplexer, **kwargs):
        """
        Handles the messages received by this consumer

        If the message contains the 'action' 'list',
        responds with the list of all the current Alarms.
        """

        if content is not None:
            if content['action'] == 'list':
                CoreConsumer.update_all_alarms_validity()
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
