import tornado
import requests
import logging
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from alarms.connectors import CdbConnector
from timers.clients import WSClient
from ias_webserver.settings import (
    BROADCAST_RATE_FACTOR,
    UNSHELVE_CHECKING_RATE,
    PROCESS_CONNECTION_PASS,
)

logger = logging.getLogger(__name__)

DEFAULT_HOSTNAME = 'localhost'
DEFAULT_PORT = '8000'
DEFAULT_MILLISECONDS_RATE = 10*1000
DEFAULT_RECONNECTION_RATE = 1000  # One second to evaluate reconnection


class Command(BaseCommand):
    """ Command used to start sending messages via websockets and http requests
    to trigger determined tasks """

    help = 'Send messages via websockets or http requests to trigger \
    determined tasks'

    def add_arguments(self, parser):
        """ Command arguments setup """
        parser.add_argument('--hostname', type=str, help='Webserver hostname')
        parser.add_argument('--port', type=str, help='Webserver port number')
        parser.add_argument('--rate', type=float,
                            help='Broadcast rate in seconds')

    def get_websocket_url(self, options):
        """
        Returns the url to send websocket messages

        Args:
            options (dict): optional arguments passed to the command

        Returns:
            string: the url
        """
        hostname = DEFAULT_HOSTNAME
        port = DEFAULT_PORT

        if options['hostname'] is not None:
            hostname = options['hostname']

        if options['port'] is not None:
            port = options['port']

        return 'ws://{}:{}/stream/?password={}'.format(
            hostname, port, PROCESS_CONNECTION_PASS
        )

    def get_http_url(self, options):
        """
        Returns the url to make http requests

        Args:
            options (dict): optional arguments passed to the command

        Returns:
            string: the url
        """
        hostname = DEFAULT_HOSTNAME
        port = DEFAULT_PORT

        if options['hostname'] is not None:
            hostname = options['hostname']

        if options['port'] is not None:
            port = options['port']

        return 'http://{}:{}/'.format(hostname, port)

    def get_websockets_tasks(self, options):
        """
        Defines the list of tasks that imply sending a message through
        websockets

        Args:
            options (dict): optional arguments passed to the command

        Returns:
            list: A list of tasks
        """
        url = self.get_websocket_url(options)
        ws_client = WSClient(url, options)

        broadcast_rate = CdbConnector.refresh_rate * BROADCAST_RATE_FACTOR
        if options['rate'] is not None:
            broadcast_rate = options['rate']*1000.0
        broadcast_rate = 500
        logger.info(
            'BROADCAST-STATUS - Sending global refresh to %s \
            every %d ms', url, broadcast_rate
        )

        def send_broadcast():
            if ws_client.is_connected():
                msg = {
                    'stream': 'broadcast',
                    'payload': {
                        'action': 'list'
                    }
                }
                ws_client.send_message(msg)

        reconnection_rate = DEFAULT_RECONNECTION_RATE

        def ws_reconnection():
            if not ws_client.is_connected():
                ws_client.reconnect()

        broadcast_task = tornado.ioloop.PeriodicCallback(
            send_broadcast,
            broadcast_rate
        )

        reconnection_task = tornado.ioloop.PeriodicCallback(
            ws_reconnection,
            reconnection_rate
        )
        return [broadcast_task, reconnection_task]

    def get_http_tasks(self, options):
        """
        Defines the list of tasks that imply an http request

        Args:
            options (dict): optional arguments passed to the command

        Returns:
            list: A list of tasks
        """
        url = self.get_http_url(options) + \
            'tickets-api/shelve-registries/check_timeouts/'
        if options['verbosity'] is not None:
            verbosity = options['verbosity']
        else:
            verbosity = 1

        unshelve_rate = UNSHELVE_CHECKING_RATE * 1000
        logger.info(
            'SHELF-TIMEOUT - Checking shelved alarms timeout from %s \
            every %d ms', url, unshelve_rate
        )

        def send_timeout():
            response = requests.put(url, data={})
            if verbosity > 1:
                logger.info('SHELF-TIMEOUT - %s', response)

        unshelve_task = tornado.ioloop.PeriodicCallback(
            sync_to_async(send_timeout),
            unshelve_rate
        )
        return [unshelve_task]

    def handle(self, *args, **options):
        """ Start periodic tasks in an ioloop"""

        websockets_tasks = self.get_websockets_tasks(options)
        http_tasks = self.get_http_tasks(options)
        # for task in websockets_tasks + http_tasks:
        for task in http_tasks:
            task.start()

        tornado.ioloop.IOLoop.current().start()
