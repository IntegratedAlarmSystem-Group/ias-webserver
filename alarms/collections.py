import time
import abc
import asyncio
from alarms.models import Alarm
from alarms.connectors import CdbConnector, TicketConnector


class AlarmCollection:
    """
    This class defines the data structure that will store and handle the Alarms
    in memory.

    Allows observers to subscribe to changes on the Alarm objects
    """

    singleton_collection = None
    """ Dictionary to store the Alarm objects, indexed by core_id """

    observers = []
    """ List to store references to the observers subscribed to changes in the
    collection """

    # Observers Methods:
    @classmethod
    def register_observer(self, observer):
        """Add an observer to the observers list"""
        if isinstance(observer, AlarmCollectionObserver):
            self.observers.append(observer)

    @classmethod
    async def notify_observers(self, alarm, action):
        """Notify to all observers an action over an alarm"""
        await asyncio.gather(
            *[observer.update(alarm, action) for observer in self.observers]
        )

    @classmethod
    async def broadcast_status_to_observers(self):
        """Notify to all observers the alarms list with its current status"""
        await asyncio.gather(
            *[observer.send_alarms_status() for observer in self.observers]
        )

    # Sync, non-notified methods:
    @classmethod
    def initialize(self, iasios=None):
        """
        Initializes the alarms collection with default alarms created
        considering the iasios core_ids or CDB iasios core_ids

        Args:
            iasios (list): A list of iasio objects

        Returns:
            dict: A dictionary of Alarm objects
        """
        if self.singleton_collection is None:
            self.singleton_collection = {}
            if iasios is None:
                iasios = CdbConnector.get_iasios(type='ALARM')
            for iasio in iasios:
                if iasio['ias_type'].upper() == 'ALARM':
                    current_time_millis = int(round(time.time() * 1000))
                    alarm = Alarm(
                        value=1,
                        mode='7',
                        validity='0',
                        core_timestamp=current_time_millis,
                        core_id=iasio['io_id'],
                        running_id='({}:IASIO)'.format(iasio['io_id'])
                    )
                    self.add(alarm)
        return self.singleton_collection

    @classmethod
    def get(self, core_id):
        """
        Returns the Alarm object in the AlarmCollection dictionary with that
        core_id value. It also initializes the Collection if it has been not
        initialized before.

        Args:
            core_id (string): the core_id of the Alarm to get

        Returns:
            dict: A dictionary of Alarm objects
        """
        if self.singleton_collection is None:
            self.initialize()
        try:
            return self.singleton_collection[core_id]
        except KeyError:
            return None

    @classmethod
    def get_all_as_dict(self):
        """Returns all the Alarms as a dictionary indexed by core_id"""
        if self.singleton_collection is None:
            self.initialize()
        return self.singleton_collection

    @classmethod
    def get_all_as_list(self):
        """Returns all the Alarms as a list"""
        return list(self.singleton_collection.values())

    @classmethod
    def add(self, alarm):
        """
        Adds the alarm to the AlarmCollection dictionary

        Args:
            alarm (Alarm): the Alarm object to delete
        """
        self.singleton_collection[alarm.core_id] = alarm

    @classmethod
    def _create_ticket(self, core_id):
        return TicketConnector.create_ticket(core_id)

    @classmethod
    def delete(self, alarm):
        """
        Deletes the Alarm object in the AlarmCollection dictionary

        Args:
            alarm (Alarm): the Alarm object to delete

        Returns:
            bool: True if the alarm was deleted,
            False if the Alarm did not exist in the collection
        """
        if alarm.core_id in self.singleton_collection:
            del self.singleton_collection[alarm.core_id]
            return True
        else:
            return False

    @classmethod
    def delete_all(self):
        """
        Deletes all the Alarm objects in the AlarmCollection dictionary. Also
        it initializes the Collection if it has been not initialized before
        """
        if self.singleton_collection is None:
            self.initialize()
            self.singleton_collection.clear()

    @classmethod
    def update(self, alarm):
        """
        Updates the Alarm object in the AlarmCollection dictionary only if
        the new Alarm instance has a later timestamp than the stored ALARM

        Args:
            alarm (Alarm): the Alarm object to update

        Returns:
            string: 'updated-different' if the alarm was different
            (besides timestamp), 'updated-equal' if it was updated but the only
            change is the timestamp, and 'nopt-updated' if it was not updated
        """
        stored_alarm = self.get(alarm.core_id)
        if alarm.core_timestamp >= stored_alarm.core_timestamp:
            alarm.ack = self.singleton_collection[alarm.core_id].ack
            self.singleton_collection[alarm.core_id] = alarm
            # Change of value must restart ack status
            if stored_alarm.value != alarm.value:
                alarm.ack = False
                # If the value chenged from clear to set,
                # a new ticket is be created
                if stored_alarm.value == 0 and alarm.value == 1:
                    self._create_ticket(alarm.core_id)

            if alarm.equals_except_timestamp(stored_alarm):
                return 'updated-equal'
            else:
                return 'updated-different'
        else:
            return 'not-updated'

    @classmethod
    def acknowledge(self, core_ids):
        """
        Acknowledges an alarm or a list of Alarms

        Args:
            core_ids (list or string): list of core_ids (or a single core_id)
            of the Alarms to acknowledge
        """
        if type(core_ids) is not list:
            core_ids = [core_ids]

        for core_id in core_ids:
            self.singleton_collection[core_id].ack = True

    @classmethod
    def reset(self, iasios=None):
        """
        Resets the AlarmCollection dictionary initializing it again. Go to
        :func:`~collections.AlarmCollection.initialize` to see the
        initialization specification.

        Args:
            iasios (list): A list of iasio objects
        """
        self.singleton_collection = None
        self.initialize(iasios)

    @classmethod
    def update_all_alarms_validity(self):
        """
        Update the validity of each alarm in the AlarmCollection dictionary. Go
        to :func:`alarms.models.Alarm.update_validity` to see the validation
        specification.

        Returns:
            dict: the AlarmCollection as a dictionary after the validity update
        """
        self.singleton_collection = {
            k: v.update_validity()
            for k, v in self.singleton_collection.items()
        }
        return self.singleton_collection

    # Async methods to handle alarm messages:
    @classmethod
    async def add_or_update_and_notify(self, alarm):
        """
        Adds the alarm if it isn't in the AlarmCollection already or updates
        the alarm in the other case. It also initializes the Collection if it
        has been not initialized before.

        Notifies the observers on either action

        Args:
            alarm (Alarm): the Alarm object to add or update

        Returns:
            message (String): a string message sumarizing what happened
        """
        if self.singleton_collection is None:
            self.initialize()
        if alarm.core_id not in self.singleton_collection:
            self.add(alarm)
            await self.notify_observers(alarm, 'create')
            return 'created-alarm'
        else:
            status = self.update(alarm)
            if status == 'not-updated':
                return 'ignored-old-alarm'
            elif status == 'updated-different':
                await self.notify_observers(alarm, 'update')
                return 'updated-alarm'
            elif status == 'updated-equal':
                return 'updated-alarm'
            else:
                raise Exception('ERROR: incorrect update status')

    @classmethod
    async def delete_and_notify(self, alarm):
        """
        Deletes the Alarm object in the AlarmCollection dictionary
        and notifies the obbservers

        Args:
            alarm (Alarm): the Alarm object to delete

        Returns:
            message (String): a string message sumarizing what happened
        """
        status = self.delete(alarm)
        if status:
            await self.notify_observers(alarm, 'delete')
            return 'deleted-alarm'
        else:
            return 'ignored-non-existing-alarm'


class AlarmCollectionObserver(abc.ABC):
    """
    This class defines an interface that all the observers must implement.
    """

    @abc.abstractmethod
    def update(alarm, action):
        pass
