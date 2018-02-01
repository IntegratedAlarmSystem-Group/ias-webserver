from django.apps import AppConfig


class AlarmConfig(AppConfig):
    """ Configuration of the application Alarm """

    name = 'alarms'

    def ready(self):
        from alarms.collections import AlarmCollection

        AlarmCollection.initialize_alarms()
