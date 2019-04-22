import logging
import requests
import tornado
from tornado.websocket import websocket_connect
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from ias_webserver.settings import UNSHELVE_CHECKING_RATE

logger = logging.getLogger(__name__)

DEFAULT_HOSTNAME = 'localhost'
DEFAULT_PORT = '8000'


class Command(BaseCommand):
    """ Command used to start sending messages via websockets and http requests
    to trigger determined tasks """

    help = 'Send messages via websockets or http requests to trigger \
    determined tasks'

    def add_arguments(self, parser):
        """ Command arguments setup """
        parser.add_argument('--hostname', type=str, help='Webserver hostname')
        parser.add_argument('--port', type=str, help='Webserver port number')

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

        http_tasks = self.get_http_tasks(options)
        for task in http_tasks:
            task.start()

        tornado.ioloop.IOLoop.current().start()
