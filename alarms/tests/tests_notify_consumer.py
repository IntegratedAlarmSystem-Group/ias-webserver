import time
import pytest
from channels.testing import WebsocketCommunicator
from alarms.models import Alarm
from alarms.consumers import NotifyConsumer
from alarms.collections import AlarmCollection
from alarms.tests.factories import AlarmFactory
from cdb.models import Iasio


class TestNotifyConsumer:
    """This class defines the test suite for the notify consumer"""

    def setup_method(self):
        """Tests setup"""
        # Arrange:
        AlarmCollection.reset([])

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_outbound_create(self):
        """Test if clients are notified when an alarm is created"""
        # Connect:
        communicator = WebsocketCommunicator(NotifyConsumer, "/notify/")
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Arrange:
        alarm = AlarmFactory.build()
        await AlarmCollection.create_or_update_if_latest(alarm)
        # Act:
        response = await communicator.receive_json_from()
        # Assert
        assert response['payload']['action'] == 'create', \
            "Action should be 'create'"
        assert response['payload']['data']['fields'] == alarm.to_dict(), \
            'Received alarm is different than expected'

#     def test_outbound_delete(self):
#         """Test if clients are notified when an alarm is deleted"""
#         # Arrange:
#         alarm = AlarmFactory()
#         self.client.receive()
#         # clean replication messsages after creation
#         self.clean_replication_messages(self.client)

#         # Act:
#         Alarm.objects.filter(pk=alarm.pk).delete()
#         received = self.client.receive()
#         # clean replication messsages after deletion
#         self.clean_replication_messages(self.client)

#         # Assert payload structure
#         self.assert_received_alarm(received, alarm)

#         # Assert action
#         self.assertEqual(
#             received['payload']['action'], 'delete',
#             "Payload aalarms.alarmction should be 'delete'"
#         )

#         # Assert that is nothing to receive
#         self.assertIsNone(
#             self.client.receive(),
#             'Received unexpected message'
#         )

#     def test_outbound_update(self):
#         """Test if clients are notified when an alarm is updated"""
#         # Arrange:
#         alarm = AlarmFactory()
#         self.client.receive()
#         # clean replication messsages after creation
#         self.clean_replication_messages(self.client)

#         # Act:
#         alarm = AlarmFactory.get_modified_alarm(alarm)
#         alarm.save()
#         received = self.client.receive()
#         # clean replication messsages after update
#         self.clean_replication_messages(self.client)

#         # Assert payload structure
#         alarm_after = Alarm.objects.get(pk=alarm.pk)
#         self.assert_received_alarm(received, alarm_after)

#         # Assert action
#         self.assertEqual(
#             received['payload']['action'], 'update',
#             "Payload action should be 'update'"
#         )

#         # Assert that is nothing to receive
#         self.assertIsNone(
#             self.client.receive(),
#             'Received unexpected message'
#         )

#     def test_msg_should_be_replicated_after_alarm_creation(self):

#         # Arrange
#         expected_messages = 1 + self.msg_replication_factor

#         # Act and assert
#         alarm = AlarmFactory()  # create alarm

#         for k in range(expected_messages):
#             received = self.client.receive()
#             self.assertNotEqual(
#                 received, None,
#                 'Expected not None message {} of {}'.format(
#                     k+1, expected_messages))
#             self.assertEqual(
#                 received['payload']['action'], 'create',
#                 "Payload action should be 'create'"
#             )
#             self.assert_received_alarm(received, alarm)

#         received = self.client.receive()
#         self.assertEqual(received, None, 'Unexpected message')

#     def test_msg_should_be_replicated_after_alarm_update(self):

#         # Arrange
#         expected_messages = 1 + self.msg_replication_factor

#         alarm = AlarmFactory()  # create alarm
#         self.client.receive()
#         # clean replication messages after creation
#         self.clean_replication_messages(self.client)

#         # Act and assert
#         alarm = AlarmFactory.get_modified_alarm(alarm)
#         alarm.save()  # update alarm
#         alarm_after = Alarm.objects.get(pk=alarm.pk)

#         for k in range(expected_messages):
#             received = self.client.receive()
#             self.assertNotEqual(
#                 received,
#                 None,
#                 'Expected not None message {} of {}'.format(
#                     k+1,
#                     expected_messages
#                     ))
#             self.assertEqual(
#                 received['payload']['action'], 'update',
#                 "Payload action should be 'update'"
#             )
#             self.assert_received_alarm(received, alarm_after)

#         received = self.client.receive()
#         self.assertEqual(received, None, 'Unexpected message')

#     def test_msg_should_be_replicated_after_alarm_deletion(self):

#         # Arrange
#         expected_messages = 1 + self.msg_replication_factor

#         alarm = AlarmFactory()  # create alarm
#         self.client.receive()
#         # clean replication messages after creation
#         self.clean_replication_messages(self.client)

#         # Act and assert
#         Alarm.objects.filter(pk=alarm.pk).delete()

#         for k in range(expected_messages):
#             received = self.client.receive()
#             self.assertNotEqual(
#                 received,
#                 None,
#                 'Expected not None message {} of {}'.format(
#                     k+1,
#                     expected_messages
#                     ))
#             self.assertEqual(
#                 received['payload']['action'], 'delete',
#                 "Payload action should be 'delete'"
#             )
#             self.assert_received_alarm(received, alarm)

#         received = self.client.receive()
#         self.assertEqual(received, None, 'Unexpected message')

    # def assert_received_alarm(self, received, alarm):
    #     """Assert if a received message corresponds to a given alarm"""
    #     self.assertIsNotNone(received, 'No message received')
    #     self.assertTrue('payload' in received, 'No payload received')
    #     self.assertTrue(
    #         'action' in received['payload'], 'Payload does not have an action'
    #     )
    #     self.assertTrue(
    #         'data' in received['payload'], 'Payload does not have data'
    #     )
    #     # check model and pk according to the binding
    #     self.assertEqual(
    #         received['payload']['model'], 'alarms.alarm',
    #         'Payload model_label does not correspond to the Alarm model'
    #     )
    #     self.assertEqual(
    #         received['payload']['pk'], alarm.pk,
    #         'Payload pk is different from alarm.pk'
    #     )
    #     # check alarms binding fields and values
    #     self.assertTrue(
    #         'value' in received['payload']['data'],
    #         'Payload does not contain value field'
    #     )
    #     self.assertTrue(
    #         'mode' in received['payload']['data'],
    #         'Payload does not contain mode field'
    #     )
    #     self.assertTrue(
    #         'core_timestamp' in received['payload']['data'],
    #         'Payload does not contain core_timestamp field'
    #     )
    #     self.assertTrue(
    #         'core_id' in received['payload']['data'],
    #         'Payload does not contain core_id field'
    #     )
    #     self.assertTrue(
    #         'running_id' in received['payload']['data'],
    #         'Payload does not contain running_id field'
    #     )
    #     self.assertEqual(
    #         received['payload']['data']['value'], alarm.value,
    #         'Payload value is different from alarm.value'
    #     )
    #     self.assertEqual(
    #         str(received['payload']['data']['mode']), alarm.mode,
    #         'Payload mode is different from alarm.mode'
    #     )
    #     self.assertEqual(
    #         received['payload']['data']['core_timestamp'],
    #         alarm.core_timestamp,
    #         'Payload core_timestamp is different from alarm.core_timestamp'
    #     )
    #     self.assertEqual(
    #         received['payload']['data']['core_id'], alarm.core_id,
    #         'Payload core_id is different from alarm.core_id'
    #     )
    #     self.assertEqual(
    #         received['payload']['data']['running_id'], alarm.running_id,
    #         'Payload running_id is different from alarm.running_id'
    #     )
