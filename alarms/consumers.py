import asyncio
import time
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from users.models import reset_auth_token
from alarms.collections import AlarmCollection, AlarmCollectionObserver
from ias_webserver.settings import PROCESS_CONNECTION_PASS

logger = logging.getLogger(__name__)


class CoreConsumer(AsyncJsonWebsocketConsumer):
    """ Consumer for messages from the core system """

    async def connect(self):
        """ Called upon connection, rejects connection if no authenticated user or password """
        if AlarmCollection.init_state == 'pending':
            AlarmCollection.initialize()
        elif AlarmCollection.init_state == 'in_progress':
            await self.close()

        # Reject connection if no authenticated user:
        if self.scope['user'].is_anonymous:
            if self.scope['password'] and \
              self.scope['password'] == PROCESS_CONNECTION_PASS:
                await self.accept()
            else:
                await self.close()
        else:
            await self.accept()

    async def receive_json(self, content, **kwargs):
        """
        Handles the messages received by this consumer.
        It delegates handling of the alarms received in the messages to :func:`~AlarmCollection.add_or_update_alarm`

        Responds with a message indicating the action taken
        (created, updated, ignored)
        """
        start = time.time()
        if not isinstance(content, list):
            content = [content]
        AlarmCollection.receive_iasios(content)
        await self.send('Received {} IASIOS'.format(len(content)))
        logger.debug('Finished receiving %d IASIOS in %1.3f seconds', len(content), time.time() - start)


class ClientConsumer(AsyncJsonWebsocketConsumer, AlarmCollectionObserver):
    """ Consumer to notify clients and listen their requests """
    groups = []

    async def connect(self):
        """
        Called upon connection, rejects connection if no authenticated user or password.
        Start the periodic notifications in the AlarmCollection
        """
        # Reject connection if no authenticated user:
        if AlarmCollection.init_state == 'pending':
            AlarmCollection.initialize()
        elif AlarmCollection.init_state == 'in_progress':
            await self.close()
        if self.scope['user'].is_anonymous:
            if self.scope['password'] and \
              self.scope['password'] == PROCESS_CONNECTION_PASS:
                AlarmCollection.register_observer(self)
                await self.accept()
            else:
                await self.close()
        else:
            AlarmCollection.register_observer(self)
            await self.accept()
        await AlarmCollection.start_periodic_tasks()

    async def update(self, payload, stream):
        """
        Notifies the client of changes in an Alarm.
        Implements the AlarmCollectionObserver.update method

        Args:
            data (dict): Dictionary that contains the 'alarms' and 'counters'
            stream (string): Stream to send the data through
        """
        message = {
            "payload": payload,
            "stream": stream,
        }
        if payload['alarms']:
            logger.debug('Sending %d alarms over stream %s'.format(len(payload['alarms']), stream))
        else:
            logger.error('Sending update with no alarms')
        await self.send_json(message)

    async def receive_json(self, content, **kwargs):
        """
        Handles the messages received by this consumer

        If the message contains the 'action' 'list', responds with the list of all the current Alarms.
        """
        if content['stream'] == 'requests':
            if content['payload'] and content['payload']['action'] is not None:
                if content['payload']['action'] == 'list':
                    await AlarmCollection.broadcast_observers()
                    logger.debug('New message received in requests stream')
                elif content['payload']['action'] == 'close':
                    await self.close()
                    reset_auth_token(self.scope['user'])
                    logger.debug('connection closed')
                else:
                    await self.send_json({
                        "payload": {
                            "data": "Unsupported action"
                        },
                        "stream": "requests",
                    })
                    logger.debug('New message received in requests stream: (unsupported action)')
        if content['stream'] == 'broadcast':
            await AlarmCollection.broadcast_observers()
            logger.debug('New message received in broadcast stream')

    async def disconnect(self, close_code):
        """
        Called when the socket closes
        """
        if self in AlarmCollection.observers:
            AlarmCollection.observers.remove(self)
