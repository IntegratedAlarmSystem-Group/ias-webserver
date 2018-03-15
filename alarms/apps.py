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
        except OperationalError:
            print('CDB is not yet defined')
