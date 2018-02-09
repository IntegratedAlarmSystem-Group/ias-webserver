import time
from django.dispatch import Signal
from alarms.models import Alarm
from cdb.models import Iasio


class AlarmCollection:

    singleton_collection = None
    observers = []

    @classmethod
    def subscribe(self, observer):
        """Add an observer to the observers list"""
        self.observers.append(observer)

    @classmethod
    async def notify_alarm(self, alarm, action):
        """Notify to all observers an action over an alarm"""
        for observer in self.observers:
            await observer.notify(alarm, action)

    @classmethod
    def initialize_alarms(self, iasios=None):
        """Initialize the alarms collection with default alarms created
        considering the iasios core_ids or CDB iasios core_ids

        Args:
            iasios (list): A list of iasio objects

        Returns:
            dict: A dictionary of Alarm objects
        """
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
        """Return the dictionary of Alarm objects"""
        if self.singleton_collection is None:
            self.initialize_alarms()
        return self.singleton_collection

    @classmethod
    def get_alarm(self, core_id):
        """Returns the Alarm object in the AlarmCollection dictionary with that
        core_id value. Also it initializes the Collection if it has been not
        initialized before."""
        if self.singleton_collection is None:
            self.initialize_alarms()
        try:
            return self.singleton_collection[core_id]
        except KeyError:
            return None

    @classmethod
    def delete_alarms(self):
        """Deletes all the Alarm objects in the AlarmCollection dictionary. Also
        it initializes the Collection if it has been not initialized before."""
        if self.singleton_collection is None:
            self.initialize_alarms()
        self.singleton_collection.clear()

    @classmethod
    def __update_if_latest(self, alarm, stored_alarm):
        """Updates the Alarm object in the AlarmCollection dictionary only if
        the new Alarm instance has a later timestamp than the stored Alarm.

        Returns:
            bool: True if the alarm instance was updated and False if it wasn't
        """
        if alarm.core_timestamp >= stored_alarm.core_timestamp:
            self.singleton_collection[alarm.core_id] = alarm
            return True
        else:
            return False

    @classmethod
    async def __create_alarm(self, alarm):
        """Adds the alarm to the AlarmCollection dictionary and notify the action
        performed to the observers"""
        self.singleton_collection[alarm.core_id] = alarm
        await self.notify_alarm(alarm, 'create')

    @classmethod
    async def create_or_update_if_latest(self, alarm):
        """Create the alarm if it isn't in the AlarmCollection or updates the
        alarm in the other case. Also it initializes the Collection if it has
        been not initialized before."""
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
        """Resets the AlarmCollection dictionary initializing it again. Go to
        :func:`~collections.AlarmCollection.initialize_alarms` to see the
        initialization specification.
        """
        self.singleton_collection = None
        self.initialize_alarms(iasios)

    @classmethod
    def get_alarms_list(self):
        """
        Get a list of all the Alarm objects in the AlarmCollection dictionary.
        """
        return list(self.singleton_collection.values())

    @classmethod
    def update_all_alarms_validity(self):
        """
        Update the validity of each alarm in the AlarmCollection dictionary. Go
        to :func:`alarms.models.Alarm.update_validity` to see the validation
        specification.
        """
        self.singleton_collection = {
            k: v.update_validity()
            for k, v in self.singleton_collection.items()
        }
        return self.singleton_collection
