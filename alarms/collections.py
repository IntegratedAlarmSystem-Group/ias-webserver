import time
import abc
import asyncio
import logging
from alarms.models import Alarm, Value
from alarms.connectors import CdbConnector, TicketConnector, PanelsConnector
from ias_webserver.settings import NOTIFICATIONS_RATE, BROADCAST_RATE_FACTOR

logger = logging.getLogger(__name__)


class AlarmCollection:
    """
    This class defines the data structure that will store and handle the Alarms
    in memory.

    Allows observers to subscribe to changes on the Alarm objects
    """

    singleton_collection = None
    """ Dictionary to store the Alarm objects, indexed by core_id """

    parents_collection = None
    """ Dictionary to store the parents of each alarm """

    values_collection = None
    """ Dictionary to store other type of values, indexed by core_id """

    alarms_views_dict = None
    """ Dictionary to store the related view names by alarm,
    indexed by core_id """

    observers = []
    """ List to store references to the observers subscribed to changes in the
    collection """

    notification_task = None
    """ Reference to the Task that notifies changes periodically """

    broadcast_task = None
    """ Reference to the Task that sends all alarms periodically """

    alarm_changes = []
    """ List of IDs of Alarms that have changed and must be notified """

    init_state = 'pending'

    # Observers Methods:
    @classmethod
    def register_observer(self, observer):
        """Add an observer to the observers list"""
        if isinstance(observer, AlarmCollectionObserver):
            self.observers.append(observer)
            logger.debug(
                'new observer was subscribed to alarm collection: %s',
                observer.__class__.__name__
            )

    @classmethod
    async def notify_observers(self):
        """ Notify to all observers an action over Alarms """
        if len(self.alarm_changes) == 0:
            return
        ids_to_notify = set(self.alarm_changes)
        self.alarm_changes = []
        alarms = [self.get(id).to_dict() for id in ids_to_notify]
        payload = {
            'alarms': alarms,
            'counters': Alarm.objects.counter_by_view()
        }
        stream = 'alarms'
        await asyncio.gather(
            *[observer.update(payload, stream) for observer in self.observers]
        )
        logger.debug(
            '%i alarms notified to all the observers', len(ids_to_notify))

    @classmethod
    async def broadcast_observers(self):
        """ Notify to all observers the alarms list with its current status """
        queryset = AlarmCollection.update_all_alarms_validity()
        alarms = []
        for item in list(queryset.values()):
            alarms.append(item.to_dict())
        payload = {
            'alarms': alarms,
            'counters': Alarm.objects.counter_by_view()
        }
        stream = 'requests',
        await asyncio.gather(
            *[observer.update(payload, stream) for observer in self.observers]
        )
        logger.debug(
            '%i alarms notified to all the observers', len(alarms))

    @classmethod
    async def periodic_notification_coroutine(self):
        """
        Coroutine that notifies of changes to all the observers periodically
        The notifications rate is defined in the variable
        ias_webserver.settings.NOTIFICATIONS_RATE
        """
        while True:
            await self.notify_observers()
            await asyncio.sleep(NOTIFICATIONS_RATE)

    @classmethod
    async def periodic_broadcast_coroutine(self, rate):
        """
        Coroutine that notifies of changes to all the observers periodically
        Args:
            rate (int): time in seconds
        """
        while True:
            await self.broadcast_observers()
            await asyncio.sleep(rate)

    @classmethod
    async def start_periodic_tasks(self):
        """
        Starts the coroutine that notifies of changes to all the observers as
        a task.

        Checks if the task (notification_task) and starts it,
        if it has not been started, or it has been cancelled or has finished
        """
        if self.notification_task is None or self.notification_task.done() or \
                self.notification_task.cancelled():
            logger.info('Starting periodic notifications')
            self.notification_task = asyncio.ensure_future(
                self.periodic_notification_coroutine())
        else:
            logger.debug('Periodic notification already started')

        if self.broadcast_task is None or self.broadcast_task.done() or \
                self.broadcast_task.cancelled():
            rate = CdbConnector.refresh_rate * BROADCAST_RATE_FACTOR / 1000
            logger.info(
                'Starting periodic broadcast with rate %d seconds', rate)
            self.broadcast_task = asyncio.ensure_future(
                self.periodic_broadcast_coroutine(rate))
        else:
            logger.debug('Periodic broadcast already started')

    @classmethod
    def record_alarm_changes(self, alarms):
        """
        Register given Alarm(s) in order to notify its(their) change(s)

        Args:
            alarms (list or Alarm): list of Alarms (or a single Alarm)
            whose changes must be notified
        """
        if not isinstance(alarms, list):
            alarms = [alarms]
        for alarm in alarms:
            self.alarm_changes.append(alarm.core_id)

    # Sync, non-notified methods:
    @classmethod
    def initialize(self, iasios=None):
        """
        Initializes the alarms collection with default alarms.
        If a list of iasios is passed, it initializes Alarms only for those
        iasios.
        If not, it initializes Alarms based on the alarm_ids used in
        AlarmConfig objects of the Panels app, getting their description and
        documentation urls from the CDB.

        Args:
            iasios (list): An optional list of iasio objects

        Returns:
            dict: A dictionary of Alarm objects
        """
        start = time.time()
        logger.info('Initializing Collection')
        if self.init_state == 'pending':
            self.init_state = 'in_progress'
            self.singleton_collection = {}
            self.parents_collection = {}
            self.values_collection = {}
            self.alarms_views_dict = \
                PanelsConnector.get_alarms_views_dict_of_alarm_configs()
            alarms_to_search = PanelsConnector.get_alarm_ids_of_alarm_configs()
            if iasios is None:
                iasios = CdbConnector.get_iasios(type='ALARM')

                for iasio in iasios:
                    if iasio['iasType'].upper() == 'ALARM':
                        alarm = self._create_alarm_from_iasio(iasio)
                        self.add(alarm)

                for alarm_id in alarms_to_search:
                    if self.get(alarm_id) is None:
                        alarm = self._create_alarm_from_iasio({'id': alarm_id})
                        self.add(alarm)
                        logger.warning(
                            alarm_id
                            + ' was not found in the CDB, initializing with '
                            + 'empty description and url '
                        )
                logger.info(
                    'the collection was initialized based on configuration')
            else:
                for iasio in iasios:
                    alarm = self._create_alarm_from_iasio(iasio)
                    self.add(alarm)
                logger.info(
                    'the collection was initialized in testing mode')
            self.init_state = 'done'
        logger.info(
            'Collection initialization finished in %d seconds',
            time.time() - start
        )
        return self.singleton_collection

    @classmethod
    def _create_alarm_from_iasio(self, iasio):
        """
        Auxiliary method used to create an Alarm from an IASIO

        Args:
            iasio (dict): A dictionary with the IASIO info

        Returns:
            alarm: an Alarm object
        """
        logger.debug(
            'creating an alarm based on iasio with id %s',
            iasio['id']
        )
        current_time = int(round(time.time() * 1000))
        if 'shortDesc' not in iasio:
            iasio['shortDesc'] = ""
        if 'docUrl' not in iasio:
            iasio['docUrl'] = ""
        if 'sound' not in iasio:
            iasio['sound'] = ""
        if 'canShelve' not in iasio:
            iasio['canShelve'] = False
        alarm_id = iasio['id']
        views = self.alarms_views_dict.get(alarm_id, [])
        alarm = Alarm(
            value=0,
            mode=7,
            validity=0,
            core_timestamp=current_time,
            core_id=alarm_id,
            running_id='({}:IASIO)'.format(alarm_id),
            description=iasio['shortDesc'],
            url=iasio['docUrl'],
            sound=iasio['sound'],
            can_shelve=self._parseBool(iasio['canShelve']),
            views=views
        )
        return alarm

    @classmethod
    def _parseBool(self, input):
        """
        Auxiliary method used to parse a field that could be either string
        or bool to bool

        Args:
            input (string or bool): the input

        Returns:
            bool: True or False
        """
        return input == "True" or input == "true" or input is True

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
        if self.init_state == 'pending':
            self.initialize()
        try:
            return self.singleton_collection[core_id]
        except KeyError:
            logger.debug(
                'the requested alarm does not exist in the collection')
            return None

    @classmethod
    def get_dependencies_recursively(self, core_id):
        """
        Returns a list of alarm ids of all the dependencies of the specified
        alarm

        Returns:
            list: A list of alarm ids dependencies of the alarm with core_id
        """
        response = []
        alarm = AlarmCollection.get(core_id)
        if alarm:
            response.append(core_id)
            for dependency_id in alarm.dependencies:
                response += AlarmCollection.get_dependencies_recursively(
                    dependency_id
                )
        logger.debug(
            'getting dependencies of alarm %s recursively: %s',
            core_id, response)
        return response

    @classmethod
    def get_ancestors_recursively(self, core_id):
        """
        Return the list of parents and grandparents recursively of the
        specified alarm

        Args:
            core_id (string): the ID of the Alarm object to get its ancestors

        Returns:
            list: List with the IDs of the ancestors
        """
        response = self._get_parents(core_id)
        for parent_id in response:
            response += self.get_ancestors_recursively(parent_id)
        logger.debug(
            'getting ancestors of alarm %s recursively: %s',
            core_id, response)
        return response

    @classmethod
    def get_all_as_dict(self):
        """
        Returns all the Alarms as a dictionary indexed by core_id

        Returns:
            dict: A dictionary of Alarms indexed by core_id
        """
        if self.init_state == 'pending':
            logger.debug('initializing the collection because it was empty')
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
            alarm (Alarm): the Alarm object to add
        """
        alarm = self._clean_alarm_dependencies(alarm)
        if alarm.value == Value.CLEARED:
            alarm.ack = TicketConnector.check_acknowledgement(
                alarm.core_id
            )
        else:
            self._unacknowledge(alarm)
        alarm.shelved = TicketConnector.check_shelve(alarm.core_id)
        self.singleton_collection[alarm.core_id] = alarm
        if alarm.core_id in self.singleton_collection.keys():
            alarm.stored = True
        self._update_parents_collection(alarm)
        Alarm.objects._update_counter_by_view_if_new_alarm_in_collection(alarm)
        logger.debug('the alarm %s was added to the collection', alarm.core_id)

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
            logger.debug('deleting alarm %s', alarm.core_id)
            del self.singleton_collection[alarm.core_id]
            logger.debug(
                'the alarm %s was deleted', alarm.core_id)
            return True
        else:
            logger.debug(
                'the alarm %s was not deleted because it did not exist')
            return False

    @classmethod
    def delete_all(self):
        """
        Deletes all the Alarm objects in the AlarmCollection dictionary. Also
        it initializes the Collection if it has been not initialized before
        """
        if self.init_state == 'pending':
            self.initialize()
            self.singleton_collection.clear()
        logger.debug('all the alarms in the collection were deleted')

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
            change is the timestamp, and 'not-updated' if it was not updated
        """
        alarm = self._clean_alarm_dependencies(alarm)
        stored_alarm = self.get(alarm.core_id)
        (notify, transition, dependencies_changed) = stored_alarm.update(alarm)
        logger.debug(
            'the alarm %s was updated in the collection', alarm.core_id)

        if dependencies_changed:
            self._update_parents_collection(alarm)
        if notify == 'not-updated':
            return notify

        if transition == 'clear-set':
            self._recursive_unacknowledge(stored_alarm.core_id)
            stored_alarm.state_change_timestamp = stored_alarm.core_timestamp
        elif transition == 'set-clear':
            self._clear_ticket(stored_alarm.core_id)
        return notify

    @classmethod
    async def acknowledge(self, core_ids):
        """
        Acknowledges an alarm or a list of Alarms

        Args:
            core_ids (list or string): list of core_ids (or a single core_id)
            of the Alarms to acknowledge

        Return:
            (list of string): list of core_ids of the acknowledged alarms
            including dependent alarms
        """
        if type(core_ids) is not list:
            core_ids = [core_ids]

        alarms = []
        alarms_ids = []
        for core_id in core_ids:
            _alarms, _alarms_ids = self._recursive_acknowledge(core_id)
            alarms += _alarms
            alarms_ids += _alarms_ids

        self.record_alarm_changes(alarms)
        logger.debug('the alarms in %s were acknowledged', alarms_ids)
        return alarms_ids

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
        self.parents_collection = None
        self.values_collection = None
        self.initialize(iasios)
        logger.debug('the alarm collection was reset')

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
        logger.debug('all the validities of the alarms were updated')
        return self.singleton_collection

    # Async methods to handle alarm messages:
    @classmethod
    def add_or_update_and_notify(self, alarm):
        """
        Adds the alarm if it isn't in the AlarmCollection already or updates
        the alarm in the other case. It also initializes the Collection if it
        has been not initialized before.

        Records the changes to be notified if it is the case

        Args:
            alarm (Alarm): the Alarm object to add or update

        Returns:
            message (String): a string message sumarizing what happened
        """
        start = time.time()
        if self.init_state == 'pending':
            self.initialize()
        if alarm.core_id not in self.singleton_collection:
            self.add(alarm)
            self.record_alarm_changes(alarm)
            response = 'created-alarm'
        else:
            status = self.update(alarm)
            if status == 'not-updated':
                response = 'ignored-old-alarm'
            elif status == 'updated-different':
                self.record_alarm_changes(alarm)
                response = 'updated-alarm'
            elif status == 'updated-equal':
                response = 'updated-alarm'
            else:
                raise Exception('ERROR: incorrect update status')
        logger.debug(
            'the alarm %s was added or updated in the collection (status %s)',
            alarm.core_id, response)
        # print('Collection,{},{}'.format(
        #     alarm.core_id, time.time() - start
        # ))
        # print('---- Collection.add_or_update, {}, {}'.format(
        #     alarm.core_id, time.time() - start
        # ))
        return response

    @classmethod
    def add_value(self, value):
        """
        Adds the value to the values collection dictionary

        Args:
            id (string): The core id of the value
            value (any): core value
        """
        self.values_collection[value.core_id] = value
        logger.debug(
            'the ias value %s was added to the values collection',
            value.core_id)

    @classmethod
    def get_value(self, core_id):
        """
        Returns the value indexed by core_id in the values collection dict

        Args:
            core_id (string): The core core_id of the value
        """
        if core_id in self.values_collection:
            return self.values_collection[core_id]
        else:
            logger.debug(
                'the ias value %s does not exist in the values collection',
                core_id)
            return None

    @classmethod
    def add_or_update_value(self, value):
        """
        Adds the ias value if it isn't in the values collection already or
        updates the ias value in the other case.

        It does not notify the observers on change. It only mantains updated
        the collection to respond to user requests.

        Args:
            value (IASValue): the IASValue object to add or update

        Returns:
            message (String): a string message sumarizing what happened
        """
        if value.core_id not in self.values_collection:
            self.add_value(value)
            status = 'created-value'
        else:
            stored_value = self.get_value(value.core_id)
            status = stored_value.update(value)
        logger.debug(
            'the value %s was added or updated in the collection (status %s)',
            value.core_id, status)
        return status

    @classmethod
    async def shelve(self, core_id):
        """
        Shelves an alarm

        Args:
            core_id (string): core_ids of the Alarm to shelve

        Returns:
            int: 1 if it was shelved, 0 if not, -1 if shelving is not allowed
        """
        alarm = self.singleton_collection[core_id]
        status = alarm.shelve()
        if status == 1:
            self.record_alarm_changes(alarm)
        logger.debug('the alarm %s was shelved (status: %s)', core_id, status)
        return status

    @classmethod
    async def unshelve(self, core_ids):
        """
        Unshelves an alarm or a list of Alarms

        Args:
            core_ids (list or string): list of core_ids (or a single core_id)
            of the Alarms to unshelve

        Returns:
            boolean: True if it was unshelved, False if not
        """
        if type(core_ids) is not list:
            core_ids = [core_ids]

        alarms = []
        for core_id in core_ids:
            alarm = self.singleton_collection[core_id]
            if alarm.unshelve():
                alarms.append(alarm)

        if alarms:
            self.record_alarm_changes(alarms)
            logger.debug('the list of alarms %s was unshelved', alarms)
            return True
        else:
            logger.debug('any of the alarm in %s was unshelved', core_ids)
            return False

    @classmethod
    def _add_parent(self, alarm_id, parent_id):
        """ Add a parent to the list of parents of the alarm

        Args:
            alarm_id (string): Core ID of the alarm
            parent_id (string): Core ID of the parent of the alarm
        """
        if alarm_id not in self.parents_collection.keys():
            self.parents_collection[alarm_id] = set()
        self.parents_collection[alarm_id].add(parent_id)
        logger.debug(
            'the alarm %s was added as a parent of alarm %s',
            parent_id, alarm_id)

    @classmethod
    def _check_dependencies_ack(self, alarm):
        """ Checks wether all the children Alarms of a given Alarm
        are acknowledged or not """
        for core_id in alarm.dependencies:
            dependency = self.singleton_collection[core_id]
            if not dependency.ack:
                logger.debug(
                    'NOT all the dependencies of alarm %s were acknowledged',
                    alarm.core_id)
                return False
        return True

    @classmethod
    def _clean_alarm_dependencies(self, alarm):
        """ Cleans the dependencies of given Alarm,
        maintaining only actual Alarms """
        dependencies = []
        for core_id in alarm.dependencies:
            if core_id in self.singleton_collection.keys():
                dependencies.append(core_id)
        alarm.dependencies = dependencies
        return alarm

    @classmethod
    def _clear_ticket(self, core_id):
        """
        Clear the open tickets for an specified Alarm ID

        Args:
            core_id (string): Core ID of the Alarm associated to the Ticket
        """
        return TicketConnector.clear_ticket(core_id)

    @classmethod
    def _create_ticket(self, core_id):
        """
        Creates a ticket for an specified Alarm ID

        Args:
            core_id (string): Core ID of the Alarm associated to the Ticket
        """
        return TicketConnector.create_ticket(core_id)

    @classmethod
    def _get_parents(self, alarm_id):
        """ Return the list of parents of the specified alarm """
        if alarm_id not in self.parents_collection.keys():
            logger.debug(
                'the list of parents is empty because the alarm %s is not in \
                the collection', alarm_id)
            return []
        else:
            return list(self.parents_collection[alarm_id])

    @classmethod
    def _recursive_acknowledge(self, core_id):
        """
        Acknowledges upstream Alarms recursively through the Alarms
        dependendy graph starting from a given Alarm
        Args:
            core_id (string): core_id of the starting Alarm
        Returns:
            array of core_ids (string) of acknowleged alarms
        """
        alarms = []
        alarms_ids = []
        if core_id in self.singleton_collection.keys():
            alarm = self.singleton_collection[core_id]
            if self._check_dependencies_ack(alarm):
                alarm.acknowledge()
                alarms.append(alarm)
                alarms_ids.append(alarm.core_id)
                for parent in self._get_parents(core_id):
                    _alarms, _alarms_ids = self._recursive_acknowledge(parent)
                    alarms += _alarms
                    alarms_ids += _alarms_ids
        logger.debug('the alarm %s were acknowledged recursively', alarms_ids)
        return alarms, alarms_ids

    @classmethod
    def _unacknowledge(self, alarm):
        """
        Unacknowledges a given Alarm

        Args:
            alarm (Alarm): The Alarm to unacknowledge
        """
        if alarm.shelved:
            logger.debug('the alarm %s was already unshelved', alarm.core_id)
            return False
        else:
            alarm.unacknowledge()
            self._create_ticket(alarm.core_id)
            logger.debug('the alarm %s was shelved', alarm.core_id)
            return True

    @classmethod
    def _recursive_unacknowledge(self, core_id):
        """
        Unacknowledges upstream Alarms recursively through the Alarms
        dependendy graph starting from a given Alarm
        Args:
            core_id (string): core_id of the starting Alarm
        Returns:
            array of core_ids (string) of unacknowleged alarms
        """
        alarms = []
        alarms_ids = []
        alarm = self.singleton_collection[core_id]
        result = self._unacknowledge(alarm)
        if result:
            alarms.append(alarm)
            alarms_ids.append(core_id)

            for parent in self._get_parents(core_id):
                _alarms, _alarms_ids = self._recursive_unacknowledge(parent)
                alarms += _alarms
                alarms_ids += _alarms_ids
        logger.debug('the alarm %s were unack recursively', alarms_ids)
        return alarms, alarms_ids

    @classmethod
    def _update_parents_collection(self, alarm):
        """ Update the parents collection according the dependencies data of
        the alarm

        Args:
            alarm (Alarm): Alarm used to update the collection
        """
        if alarm.dependencies:
            for dependency in alarm.dependencies:
                self._add_parent(dependency, alarm.core_id)
        logger.debug('update parents of alarm %s', alarm.core_id)


class AlarmCollectionObserver(abc.ABC):
    """
    This class defines an interface that all the observers must implement.
    """

    @abc.abstractmethod
    def update(data, stream):
        """
        Method that will be called on Observers when there is a new action
        to notifiy

        Args:
            data (dict): Dictionary that contains the 'alarms' and 'counters'
            stream (string): Stream to send the data through
        """
        pass
