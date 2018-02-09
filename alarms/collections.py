import time
from django.dispatch import Signal
from alarms.models import Alarm
from cdb.models import Iasio


class AlarmCollection:

    singleton_collection = None
    observers = []

    @classmethod
    def subscribe(self, observer):
        self.observers.append(observer)

    @classmethod
    async def notify_alarm(self, alarm, action):
        for observer in self.observers:
            await observer.notify(alarm, action)

    @classmethod
    def initialize_alarms(self, iasios=None):
        if self.singleton_collection is None:
            self.singleton_collection = {}
            if iasios is None:
                iasios = Iasio.objects.filter(ias_type='ALARM')
            for iasio in iasios:
                if iasio.ias_type.upper() == 'ALARM':
                    current_time_millis = int(round(time.time() * 1000))
                    alarm = Alarm(
                        value=1,
                        mode='7',
                        validity='0',
                        core_timestamp=current_time_millis,
                        core_id=iasio.io_id,
                        running_id='({}:IASIO)'.format(iasio.io_id)
                    )
                    self.__create_alarm(alarm)
        return self.singleton_collection

    @classmethod
    def get_alarms(self):
        if self.singleton_collection is None:
            self.initialize_alarms()
        return self.singleton_collection

    @classmethod
    def get_alarm(self, core_id):
        if self.singleton_collection is None:
            self.initialize_alarms()
        try:
            return self.singleton_collection[core_id]
        except KeyError:
            return None

    @classmethod
    def delete_alarms(self):
        if self.singleton_collection is None:
            self.initialize_alarms()
        self.singleton_collection.clear()

    @classmethod
    def __update_if_latest(self, alarm, stored_alarm):
        if alarm.core_timestamp >= stored_alarm.core_timestamp:
            self.singleton_collection[alarm.core_id] = alarm
            return True
        else:
            return False

    @classmethod
    async def __create_alarm(self, alarm):
        self.singleton_collection[alarm.core_id] = alarm
        await self.notify_alarm(alarm, 'create')

    @classmethod
    async def create_or_update_if_latest(self, alarm):
        if self.singleton_collection is None:
            self.initialize_alarms()
        stored_alarm = self.get_alarm(alarm.core_id)
        if not stored_alarm:
            await self.__create_alarm(alarm)
            return 'created-alarm'
        else:
            if self.__update_if_latest(alarm, stored_alarm):
                return 'updated-alarm'
            else:
                return 'ignored-old-alarm'

    @classmethod
    def reset(self, iasios=None):
        self.singleton_collection = None
        self.initialize_alarms(iasios)

    @classmethod
    def get_alarms_list(self):
        return list(self.singleton_collection.values())

    @classmethod
    def update_all_alarms_validity(self):
        self.singleton_collection = {
            k: v.update_validity()
            for k, v in self.singleton_collection.items()
        }
        return self.singleton_collection
