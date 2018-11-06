import os
import logging
from django.apps import AppConfig
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


class AlarmConfig(AppConfig):
    """ Configuration of the application Alarm """

    name = 'alarms'
    """ Name of the application """

    def ready(self):
        """ Initializes AlarmCollection on application start """
        if os.environ.get('TESTING', False):
            logger.info(
                'Running in testing mode. Collections were not initialized.')
            return
        from alarms.collections import AlarmCollection
        try:
            AlarmCollection.initialize()
        except (OperationalError, TypeError) as e:
            logger.warning('AlarmCollection was not initialized. %s', e)

        from alarms.connectors import CdbConnector
        try:
            CdbConnector.initialize_ias(pk=1)
        except (OperationalError, TypeError) as e:
            logger.warning('CDB Configuration was not initialized. %s', e)
