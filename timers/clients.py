import json
import logging
from tornado.websocket import websocket_connect

logger = logging.getLogger(__name__)


class WSClient():
    """ Tornado based websocket client """

    def __init__(self, url, options):
        self.url = url
        self.options = options
        self.connection = None
        self.websocket_connect = None

    def start_connection(self):
        return websocket_connect(
            self.url,
            callback=self.on_open,
            on_message_callback=self.on_message
        )

    def on_open(self, f):
        try:
            self.connection = f.result()
            logger.info('websocket client connected')
        except Exception as e:
            logger.error(e)
            self.websocket_connect = None

    def on_message(self, message):
        """ Callback on message
        Note: None message is received if the connection is closed.
        """
        if self.options['verbosity'] and self.options['verbosity'] > 1:
            logger.info("Echo: {}".format(message))
        if message is None:
            logger.error('Problem with the connection. Connection closed.')
            self.connection = None
            self.websocket_connect = None

    def reconnect(self):
        """ Reconnection method
        This method is intended to be used by a tornado periodic callback
        if there is no valid websocket client
        """
        logger.info('try websocket client reconnection')
        self.websocket_connect = self.start_connection()

    def is_connected(self):
        if self.connection is None:
            return False
        else:
            return True

    def send_message(self, message):
        """ Sends a message """
        self.connection.write_message(json.dumps(message))
