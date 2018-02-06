from channels.test import ChannelTestCase, WSClient, apply_routes
from .factories import AlarmFactory
from ..models import Alarm, AlarmBinding
from ..collections import AlarmCollection
from cdb.models import Iasio
from ..consumers import AlarmDemultiplexer, AlarmRequestConsumer, CoreConsumer
from channels.routing import route
import time


def gen_aux_dict_from_object(obj):
    """
    Generate and return a dict without hidden fields and id from an Object
    """
    ans = {}
    for key in obj.__dict__:
        if key[0] != '_' and key != 'id':
            ans[key] = obj.__dict__[key]
    return ans


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
