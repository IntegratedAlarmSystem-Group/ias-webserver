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
        from alarms.connectors import CdbConnector
        try:
            CdbConnector.initialize_ias(pk=1)
        except (OperationalError, TypeError) as e:
            logger.warning('CDB Configuration was not initialized. %s', e)
