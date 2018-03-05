from django.apps import AppConfig


class AlarmConfig(AppConfig):
    """ Configuration of the application Alarm """

    name = 'alarms'
    """ Name of the application """

    def ready(self):
        """ Initializes AlarmCollection on application start """
        from alarms.collections import AlarmCollection
        AlarmCollection.initialize()
