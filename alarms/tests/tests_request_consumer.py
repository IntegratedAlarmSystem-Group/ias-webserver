import pytest
from channels.testing import HttpCommunicator
# from channels.testing import ChannelTestCase, WSClient, apply_routes
from .factories import AlarmFactory
from ..collections import AlarmCollection
from cdb.models import Iasio
from ..consumers import AlarmDemultiplexer, AlarmRequestConsumer
from channels.routing import route
from freezegun import freeze_time
import datetime


class TestAlarmRequestConsumer(ChannelTestCase):
    """This class defines the test suite for the channels alarm requests"""

    def setUp(self):
        """TestCase setup"""
        # Arrange:
        self.client = WSClient()
        Iasio.objects.all().delete()
        AlarmCollection.reset()

    def test_alarms_list(self):
        """Test if clients can request and receive a list of alarms"""
        # Arrange:
        expected_alarms_count = 3
        for k in range(expected_alarms_count):
            AlarmCollection.create_or_update_if_latest(AlarmFactory.build())
        # Act:
        with apply_routes([AlarmDemultiplexer.as_route(path='/'),
                          route("requests", AlarmRequestConsumer)]):
            client = WSClient()
            client.send_and_consume('websocket.connect', path='/')
            client.receive()
            client.send_and_consume('websocket.receive', path='/', text={
                'stream': 'requests',
                'payload': {
                    'action': 'list'
                }
            })
            response = client.receive()
        # Assert:
        expected_alarms_list = []
        alarms = AlarmCollection.get_alarms()
        for core_id, alarm in alarms.items():
            expected_alarms_list.append({
                'pk': None,
                'model': 'alarms.alarm',
                'fields': alarm.to_dict()
            })
        alarms_list = response['payload']['data']
        self.assertEqual(
            alarms_list, expected_alarms_list,
            'The received alarms are different than the alarms in the DB'
        )

    def test_alarms_list_validity(self):
        """Test if clients receive a list of alarms with updated validity"""
        initial_time = datetime.datetime.now()
        with freeze_time(initial_time) as frozen_datetime:
            # Arrange:
            expected_alarms_count = 3
            for k in range(expected_alarms_count):
                valid_alarm = AlarmFactory.get_valid_alarm()
                AlarmCollection.create_or_update_if_latest(valid_alarm)
            expected_alarms_list = []
            alarms = AlarmCollection.get_alarms()
            for core_id, alarm in alarms.items():
                alarm_dict = alarm.to_dict()
                alarm_dict['validity'] = '0'
                expected_alarms_list.append({
                    'pk': None,
                    'model': 'alarms.alarm',
                    'fields': alarm_dict
                })
            # Act:
            max_timedelta = datetime.timedelta(seconds=10)
            frozen_datetime.tick(delta=max_timedelta)
            with apply_routes([AlarmDemultiplexer.as_route(path='/'),
                               route("requests", AlarmRequestConsumer)]):
                client = WSClient()
                client.send_and_consume('websocket.connect', path='/')
                client.receive()
                client.send_and_consume('websocket.receive', path='/', text={
                    'stream': 'requests',
                    'payload': {
                        'action': 'list'
                    }
                })
                response = client.receive()
            # Assert:
            alarms_list = response['payload']['data']
            self.assertEqual(
                alarms_list, expected_alarms_list,
                'The alarms was not invalidated as expected after 10 seconds'
            )

    def test_unsupported_action(self):
        """Test if clients can request and receive a list of alarms"""
        # Arrange:
        # Act:
        with apply_routes([AlarmDemultiplexer.as_route(path='/'),
                          route("requests", AlarmRequestConsumer)]):
            client = WSClient()
            client.send_and_consume('websocket.connect', path='/')
            client.receive()
            client.send_and_consume('websocket.receive', path='/', text={
                'stream': 'requests',
                'payload': {
                    'action': 'other_action'
                }
            })
            response = client.receive()
        # Assert:
        expected_message = 'Unsupported action'
        response_message = response['payload']['data']
        self.assertEqual(
            response_message, expected_message,
            'The received alarms are different than the alarms in the DB'
        )
