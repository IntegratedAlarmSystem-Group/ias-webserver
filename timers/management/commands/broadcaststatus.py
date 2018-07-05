"""
Broadcast alarm status command

Command developed to broadcast the alarms list to clients
subscribed to the webserver stream according to a selected rate

"""

import json
import tornado
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from django.urls import reverse
from rest_framework.test import APIClient
from ias_webserver.settings import BROADCAST_RATE_FACTOR
from timers.clients import WSClient
from alarms.connectors import CdbConnector

DEFAULT_HOSTNAME = 'localhost'
DEFAULT_PORT = '8000'
DEFAULT_MILLISECONDS_RATE = 10*1000
DEFAULT_UNSHELVE_RATE = 60000
DEFAULT_RECONNECTION_RATE = 1000  # One second to evaluate reconnection


class Command(BaseCommand):
    help = 'Send a message via websockets to trigger the broadcast for the \
    current alarms list'

    def add_arguments(self, parser):
        """ Command arguments setup """
        parser.add_argument('--hostname', type=str, help='Webserver hostname')
        parser.add_argument('--port', type=str, help='Webserver port number')
        parser.add_argument('--rate', type=float,
                            help='Broadcast rate in seconds')
        parser.add_argument('--verbose', type=bool, default=False,
                            help='Print option for received messages')

    def get_websocket_url(self, options):
        """ Returns websocket url of the ias webserver """

        hostname = DEFAULT_HOSTNAME
        port = DEFAULT_PORT

        if options['hostname'] is not None:
            hostname = options['hostname']

        if options['port'] is not None:
            port = options['port']

        return 'ws://{}:{}/stream/'.format(hostname, port)

    def get_http_url(self, options):
        """ Returns http url of the ias webserver """

        hostname = DEFAULT_HOSTNAME
        port = DEFAULT_PORT

        if options['hostname'] is not None:
            hostname = options['hostname']

        if options['port'] is not None:
            port = options['port']

        return 'http://{}:{}/'.format(hostname, port)

    def get_websockets_tasks(self, options):
        url = self.get_websocket_url(options)
        ws_client = WSClient(url, options)

        broadcast_rate = CdbConnector.refresh_rate * BROADCAST_RATE_FACTOR
        if options['rate'] is not None:
            broadcast_rate = options['rate']*1000.0
        log = 'BROADCAST-STATUS | Sending global refresh to {} \
            every {} milliseconds'.format(url, broadcast_rate)
        print(log)

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
        api = APIClient()
        url = self.get_http_url(options)

        unshelve_rate = DEFAULT_UNSHELVE_RATE
        log = 'SHELF-TIMEOUT | Checking shelved alarms timeout from {} \
            every {} milliseconds'.format(url, unshelve_rate)
        print(log)

        def send_timeout():
            url = reverse('shelveregistry-check-timeouts')
            response = api.put(url, {}, format="json")
            print('SHELF-TIMEOUT | ', response)

        unshelve_task = tornado.ioloop.PeriodicCallback(
            sync_to_async(send_timeout),
            unshelve_rate
        )
        return [unshelve_task]

    def handle(self, *args, **options):
        """ Start periodic task and related ioloop"""

        websockets_tasks = self.get_websockets_tasks(options)
        http_tasks = self.get_http_tasks(options)
        for task in websockets_tasks + http_tasks:
            task.start()

        tornado.ioloop.IOLoop.current().start()
