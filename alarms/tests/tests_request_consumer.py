import datetime
import pytest
from freezegun import freeze_time
from channels.testing import WebsocketCommunicator
from alarms.tests.factories import AlarmFactory
from alarms.collections import AlarmCollection
from alarms.consumers import AlarmRequestConsumer


class TestAlarmRequestConsumer:
    """This class defines the test suite for the AlarmRequestConsumer"""

    def setup_method(self):
        """Tests setup"""
        # Arrange:
        AlarmCollection.reset([])

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_alarms_list(self):
        """Test if clients can request and receive a list of alarms"""
        # Connect:
        communicator = WebsocketCommunicator(AlarmRequestConsumer, "/stream/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Arrange:
        expected_alarms_count = 3
        for k in range(expected_alarms_count):
            AlarmCollection.create_or_update_if_latest(AlarmFactory.build())
        # Act:
        msg = {
            'stream': 'requests',
            'payload': {
                'action': 'list'
            }
        }
        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()
        # Assert:
        expected_alarms_list = []
        alarms = AlarmCollection.get_alarms()
        for core_id, alarm in alarms.items():
            expected_alarms_list.append({
                'pk': None,
                'model': 'alarms.alarm',
                'fields': alarm.to_dict()
            })
        alarms_list = response['data']
        assert alarms_list == expected_alarms_list, \
            'The received alarms are different than the alarms in the Server'
        # Close:
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_alarms_list_validity(self):
        """Test if clients receive a list of alarms with updated validity"""
        # Connect:
        communicator = WebsocketCommunicator(AlarmRequestConsumer, "/stream/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Arrange:
        initial_time = datetime.datetime.now()
        with freeze_time(initial_time) as frozen_datetime:
            # create 3 valid alarms
            # and stored them as invalid in expected_alarms:
            expected_alarms_count = 3
            expected_alarms_list = []
            for k in range(expected_alarms_count):
                valid_alarm = AlarmFactory.get_valid_alarm()
                AlarmCollection.create_or_update_if_latest(valid_alarm)
                alarm_dict = valid_alarm.to_dict()
                alarm_dict['validity'] = '0'
                expected_alarms_list.append({
                    'pk': None,
                    'model': 'alarms.alarm',
                    'fields': alarm_dict
                })
            # Act:
            msg = {
                'stream': 'requests',
                'payload': {
                    'action': 'list'
                }
            }
            # make request 10 seconds after alarms were created:
            max_timedelta = datetime.timedelta(seconds=10)
            frozen_datetime.tick(delta=max_timedelta)
            await communicator.send_json_to(msg)
            response = await communicator.receive_json_from()
            # Assert:
            alarms_list = response['data']
            assert alarms_list == expected_alarms_list, \
                'The alarms were not invalidated as expected after 10 seconds'
        # Close:
        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_unsupported_action(self):
        """
        Test if clients receive 'Unsupported action' when action is not 'list'
        """
        # Connect:
        communicator = WebsocketCommunicator(AlarmRequestConsumer, "/stream/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Act:
        msg = {
            'stream': 'requests',
            'payload': {
                'action': 'other action'
            }
        }
        await communicator.send_json_to(msg)
        response = await communicator.receive_json_from()
        # Assert:
        expected_message = 'Unsupported action'
        response_message = response['data']
        assert response_message == expected_message, \
            'The response was not the expected'
