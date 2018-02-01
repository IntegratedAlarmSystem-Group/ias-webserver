from alarms.models import Alarm
from cdb.models import Iasio
import time


class AlarmCollection:

    singleton_collection = {}

    @classmethod
    def initialize_alarms(self):
        if not self.singleton_collection:
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
                self.create_or_update_alarm(alarm)
        return self.singleton_collection

    @classmethod
    def get_alarms(self):
        return self.singleton_collection

    @classmethod
    def delete_alarms(self):
        self.singleton_collection.clear()

    @classmethod
    def create_or_update_alarm(self, alarm):
        self.singleton_collection[alarm.core_id] = alarm
