from alarms.models import Alarm
from cdb.models import Iasio
import time


class AlarmCollection:

    singleton_collection = None

    @classmethod
    def initialize_alarms(self):
        if self.singleton_collection is None:
            self.singleton_collection = {}
            for iasio in Iasio.objects.filter(ias_type='ALARM'):
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
        except:
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
    def __create_alarm(self, alarm):
        self.singleton_collection[alarm.core_id] = alarm

    @classmethod
    def create_or_update_if_latest(self, alarm):
        if self.singleton_collection is None:
            self.initialize_alarms()
        stored_alarm = self.get_alarm(alarm.core_id)
        if not stored_alarm:
            self.__create_alarm(alarm)
            return 'created-alarm'
        else:
            if self.__update_if_latest(alarm, stored_alarm):
                return 'updated-alarm'
            else:
                return 'ignored-old-alarm'

    @classmethod
    def reset(self):
        self.singleton_collection = None
        self.initialize_alarms()

    @classmethod
    def get_alarms_list(self):
        return list(self.singleton_collection.values())
