from django.apps import AppConfig
from django.db.utils import OperationalError


class AlarmConfig(AppConfig):
    """ Configuration of the application Alarm """

    name = 'alarms'
    """ Name of the application """

    def ready(self):
        """ Initializes AlarmCollection on application start """
        from alarms.collections import AlarmCollection
        try:
            AlarmCollection.initialize()
        except (OperationalError, TypeError) as e:
            print('WARN:', e)

        from alarms.connectors import CdbConnector
        try:
            CdbConnector.initialize_ias(pk=1)
        except (OperationalError, TypeError) as e:
            print('WARN:', e)
