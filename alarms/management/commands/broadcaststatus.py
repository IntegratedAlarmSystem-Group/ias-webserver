"""
Broadcast alarm status command

Command developed to broadcast the alarms list to clients
subscribed to the webserver stream according to a selected rate

"""

import json

from django.core.management.base import BaseCommand, CommandError

import tornado
from tornado import ioloop
from tornado.websocket import websocket_connect

DEFAULT_HOSTNAME = 'localhost'
DEFAULT_PORT = '8000'
DEFAULT_MILLISECONDS_RATE = 1000


class WSClient(tornado.websocket.WebSocketHandler):
    def __init__(self, url):
        self.connection = None
        self.url = url
        self.ws = websocket_connect(
            self.url,
            callback=self.on_open,
            on_message_callback=self.on_message
        )

    def on_open(self, f):
        try:
            self.connection = f.result()
        except Exception as e:
            print(e)

    def on_message(self, message):
        print("Echo: {}".format(message))

    def on_close(self):
        print("Closed connection.")


class Command(BaseCommand):
    help = 'Send a message via websockets to trigger the broadcast for the current alarms list'

    def add_arguments(self, parser):
        parser.add_argument('--hostname', type=str, help='Webserver hostname')
        parser.add_argument('--port', type=str, help='Webserver port number')
        parser.add_argument('--rate', type=str, help='Broadcast rate in seconds')

    def get_websocket_url(self, options):

        hostname = DEFAULT_HOSTNAME
        port = DEFAULT_PORT

        if options['hostname'] is not None:
            hostname = options['hostname']

        if options['port'] is not None:
            port = options['port']

        return 'ws://{}:{}/stream/'.format(hostname, port)

    def handle(self, *args, **options):

        milliseconds_rate = DEFAULT_MILLISECONDS_RATE

        if options['rate'] is not None:
            milliseconds_rate = options['rate']/(1000.0)

        url = self.get_websocket_url(options)

        ws = WSClient(url)

        def trigger_broadcast():
            if ws.connection is not None:
                msg = {
                    'stream': 'broadcast',
                    'payload': {
                        'action': 'list'
                    }
                }
                ws.connection.write_message(json.dumps(msg))

        task = tornado.ioloop.PeriodicCallback(
            trigger_broadcast,
            milliseconds_rate
        )
        task.start()

        tornado.ioloop.IOLoop.current().start()
