import datetime
import pytest
from freezegun import freeze_time
from channels.testing import WebsocketCommunicator
from alarms.consumers import ClientConsumer
from alarms.collections import AlarmCollection
from alarms.tests.factories import AlarmFactory


class TestPeriodicBroadcastCase:
    """This class defines the test suite for periodic notification of changes
    to consumer clients"""

    def setup_method(self):
        """TestCase setup, executed before each test of the TestCase"""
        # Arrange:
        AlarmCollection.reset([])

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_outbound_create(self):

        # Connect:
        communicator = WebsocketCommunicator(ClientConsumer, "/stream/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'

        communicator_observer = WebsocketCommunicator(ClientConsumer, "/stream/")
        connected_observer, subprotocol_observer = await communicator.connect()
        assert connected_observer, 'The communicator was not connected'

        # Arrange:
        initial_time = datetime.datetime.now()
        with freeze_time(initial_time) as frozen_datetime:
            # create 3 valid alarms
            # and stored them as invalid in expected_alarms:
            expected_alarms_count = 3
            expected_alarms_list = []
            for k in range(expected_alarms_count):
                valid_alarm = AlarmFactory.get_valid_alarm()
                AlarmCollection.add(valid_alarm)
                alarm_dict = valid_alarm.to_dict()
                alarm_dict['validity'] = '0'
                expected_alarms_list.append(alarm_dict)
            # Act:
            msg = {
                'stream': 'broadcast',
                'payload': {
                    'action': 'list'
                }
            }
            # make request 10 seconds after alarms were created:
            max_timedelta = datetime.timedelta(seconds=10)
            frozen_datetime.tick(delta=max_timedelta)
            await communicator.send_json_to(msg)
            response = await communicator.receive_json_from()
            response_observer = await communicator_observer.receive_json_from()

            # Assert:
            alarms_list = response_observer['payload']['data']
            sorted_alarms_list = sorted(alarms_list,
                                        key=lambda k: k['core_id'])
            sorted_expected_alarms_list = sorted(expected_alarms_list,
                                                 key=lambda k: k['core_id'])
            assert sorted_alarms_list == sorted_expected_alarms_list, \
                'The alarms were not invalidated as expected after 10 seconds'
        # Close:
        await communicator.disconnect()
        await communicator_observer.disconnect()
