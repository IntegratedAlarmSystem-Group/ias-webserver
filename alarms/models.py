import time
import logging
from collections import Counter
from utils.choice_enum import ChoiceEnum
from alarms.connectors import CdbConnector

logger = logging.getLogger(__name__)


class OperationalMode(ChoiceEnum):
    """ Operational Mode of a monitor point value. """

    STARTUP = 0
    INITIALIZATION = 1
    CLOSING = 2
    SHUTTEDDOWN = 3
    MAINTENANCE = 4
    OPERATIONAL = 5
    DEGRADED = 6
    UNKNOWN = 7
    MALFUNCTIONING = 8

    @classmethod
    def options(cls):
        """ Return a list of tuples with the valid options. """
        return cls.get_choices()


class Value(ChoiceEnum):
    """ Value of the Alarm. """

    SET_CRITICAL = 4
    SET_HIGH = 3
    SET_MEDIUM = 2
    SET_LOW = 1
    CLEARED = 0

    @classmethod
    def options(cls):
        """ Return a list of tuples with the valid options. """
        return cls.get_choices()

    @classmethod
    def unset_options(cls):
        """ Return a list of tuples with the valid options. """
        return [0]


class Validity(ChoiceEnum):
    """ Possible validity states of an Alarm """

    RELIABLE = 1
    """ The value has been provided in time and the operator can trust what
    the IAS shows"""

    UNRELIABLE = 0
    """ The values has not been produced in time either by the IAS Core or due
    to network problems or any other reason."""

    @classmethod
    def options(cls):
        """ Returns a list of tuples with the valid options. """
        return cls.get_choices()


class AlarmCountManager:
    """ Class to manage the counter by view. """

    counter_by_view = {}

    def reset_counter_by_view(self):
        """ Method to clear the counter by view """
        self.counter_by_view = {}

    def update_counter_by_view_if_new_alarm_in_collection(self, alarm):
        """ Increase counter for a new SET UNACK alarm
            Note: This method is used in the AlarmCollection
        """
        if alarm.is_stored():
            views = alarm.views
            current_views = self.counter_by_view.keys()
            for view in views:
                # initialize count if no key
                if view not in current_views:
                    self.counter_by_view[view] = 0
                    current_views = self.counter_by_view.keys()
                # update count
                if alarm.value > 0:
                    if alarm.ack is not True:
                        # unacknowledged alarm in set status
                        self.counter_by_view[view] += 1

    def update_counter_by_view_if_alarm_is_acknowledged(self, after_ack_alarm, initial_ack_state):
        """ Update counter after acknowledgment action """
        alarm = after_ack_alarm
        if alarm.is_stored():
            views = alarm.views
            current_views = self.counter_by_view.keys()
            for view in views:
                # initialize count if no key
                if view not in current_views:
                    self.counter_by_view[view] = 0
                    current_views = self.counter_by_view.keys()
                if alarm.value > 0:
                    # set alarm
                    if initial_ack_state is False:
                        # from unack state
                        if alarm.ack is True:
                            # to ack state
                            self.counter_by_view[view] -= 1
                else:
                    # cleared alarm
                    if initial_ack_state is False:
                        # from unack state
                        if alarm.ack is True:
                            # to ack state
                            self.counter_by_view[view] += 0

    def update_counter_by_view_if_alarm_is_unacknowledged(
        self, after_ack_alarm, initial_ack_state
    ):
        """ Update counter after unacknowledgment action """
        alarm = after_ack_alarm
        if alarm.is_stored():
            views = alarm.views
            current_views = self.counter_by_view.keys()
            for view in views:
                # initialize count if no key
                if view not in current_views:
                    self.counter_by_view[view] = 0
                    current_views = self.counter_by_view.keys()
                if alarm.value > 0:
                    # set alarm
                    if initial_ack_state is True:
                        # from ack state
                        if alarm.ack is False:
                            # to unack state
                            self.counter_by_view[view] += 1
                else:
                    # cleared alarm
                    if initial_ack_state is True:
                        # from ack state
                        if alarm.ack is False:
                            # to unack state
                            self.counter_by_view[view] += 0

    def update_counter_by_view_if_alarm_has_value_update(
        self, alarm, initial_ack_state, transition
    ):
        """ Update counter after value (set or cleared) update """
        if alarm.is_stored():
            views = alarm.views
            current_views = self.counter_by_view.keys()
            for view in views:
                # initialize count if no key
                if view not in current_views:
                    self.counter_by_view[view] = 0
                    current_views = self.counter_by_view.keys()
                if transition == 'clear-set':
                    # set alarm
                    if initial_ack_state is False:
                        # from ack state
                        if alarm.ack is False:
                            # to unack state
                            self.counter_by_view[view] += 1
                if transition == 'set-clear':
                    # cleared alarm
                    if initial_ack_state is False:
                        # from ack state
                        if alarm.ack is False:
                            # to unack state
                            self.counter_by_view[view] -= 1


class AlarmManager(AlarmCountManager):
    """ Set of auxiliary methods for the alarm model. """


class Alarm:
    """ Alarm generated by some device in the observatory. """

    objects = AlarmManager()

    def __init__(self, core_timestamp, core_id, running_id, value=0, mode=0,
                 validity=0, dependencies=[], properties={}, timestamps={},
                 ack=False, shelved=False, state_change_timestamp=0,
                 description='', url='', sound='', can_shelve=False, views=[],
                 stored=False, value_change_timestamp=0,
                 value_change_transition=[0, 0]):
        """ Constructor of the class,
        only executed when there a new instance is created.
        Receives and validates values for the attributes of the object """

        self.core_timestamp = core_timestamp
        """ Core timestamp of the alarm """

        self.core_id = core_id
        """ Core ID of the alarm """

        self.running_id = running_id
        """ Running ID of the alarm """

        self.value = value
        """ Value of the alarm """

        self.mode = mode
        """ Operational mode of the alarm """

        self.validity = validity
        """ Validity of the alarm """

        self.dependencies = dependencies  # optiona
        """ Children Alarms, alarms on which this Alarm depends """

        self.properties = properties      # optiona
        """ Properties of the core """

        self.timestamps = timestamps      # optiona
        """ Timestamps of the core """

        self.ack = ack
        """ True if the alarm is acknowledged, False if not """

        self.shelved = shelved
        """ True if the alarm is shelved, False if not """

        self.state_change_timestamp = state_change_timestamp
        """ Timestamp of the last important (notified) change in the alarm """

        self.description = description
        """ Description of the alarm """

        self.url = url
        """ URL to go for documentation of the alarm """

        self.sound = sound
        """ Sound associated to the alarm """

        self.can_shelve = can_shelve
        """ Flag that defines weteher or not the alarm can be shelved """

        self.views = views  # optional
        """List of views for which the alarm must be considered for counting"""

        self.stored = stored
        """ Flag that defines weteher or not the alarm is stored """

        self.value_change_timestamp = value_change_timestamp
        """ Timestamp of the last change in the alarm value """

        self.value_change_transition = value_change_transition
        """
        Transition of the last change in the alarm value
        Stored as a list with 2 elements in order: [previous_value, new_value]
        """

    def __str__(self):
        """ Returns a string representation of the object """
        return str(self.core_id) + '=' + str(self.value)

    def to_dict(self):
        """ Returns a dict with all the values of the different attributes """
        return {
            'value': self.value,
            'mode': self.mode,
            'validity': self.validity,
            'core_timestamp': self.core_timestamp,
            'state_change_timestamp': self.state_change_timestamp,
            'core_id': self.core_id,
            'running_id': self.running_id,
            'timestamps': self.timestamps,
            'properties': self.properties,
            'dependencies': self.dependencies,
            'ack': self.ack,
            'shelved': self.shelved,
            'description': self.description,
            'url': self.url,
            'sound': self.sound,
            'can_shelve': self.can_shelve,
            'value_change_timestamp': self.value_change_timestamp,
            'value_change_transition': self.value_change_transition,
        }

    def update(self, alarm):
        """
        Updates the alarm with attributes from another given alarm if the
        timestamp of the given alarm is greater than the stored alarm.

        Args:
            alarm (Alarm): The new alarm object

        Returns:
            (string, string, boolean): A tuple with the state of the update
            (not-updated, updated-equal, updated-different), the
            transition of the alarm value (clear-set, set-clear or None) and
            wether or not the dependencies of the alarm have been updated
        """
        initial_ack_state = self.ack  # counter by view variable

        if alarm.core_timestamp <= self.core_timestamp:
            logger.debug(
                'alarm %s was not updated (tstamp is older than the last one)',
                alarm.core_id)
            return ('not-updated', None, False)

        # Evaluate alarm state transition between set and unset states:
        if self.value == 0 and alarm.value > 0:
            transition = 'clear-set'
        elif self.value > 0 and alarm.value == 0:
            transition = 'set-clear'
        else:
            transition = None

        if self.mode != alarm.mode or \
           (self.state_change_timestamp == 0 and alarm.validity == 1):
            self.state_change_timestamp = alarm.core_timestamp

        if self.value != alarm.value:
            self.state_change_timestamp = alarm.core_timestamp
            self.value_change_timestamp = alarm.core_timestamp
            self.value_change_transition = [self.value, alarm.value]

        ignored_fields = ['core_timestamp', 'id', 'timestamps']
        unchanged_fields = \
            ['ack', 'shelved', 'description', 'url', 'sound', 'can_shelve',
                'state_change_timestamp', 'views', 'stored',
                'value_change_timestamp', 'value_change_transition']

        notify = 'updated-equal'
        if Counter(self.dependencies) == Counter(alarm.dependencies):
            dependencies_changed = True
        else:
            dependencies_changed = False

        for field in alarm.__dict__.keys():
            if field in unchanged_fields:
                continue
            old_value = getattr(self, field)
            new_value = getattr(alarm, field)
            if (field not in ignored_fields) and old_value != new_value:
                notify = 'updated-different'
            setattr(self, field, new_value)

        # start block - counter by view
        self.objects.update_counter_by_view_if_alarm_has_value_update(self, initial_ack_state, transition)
        # end block - counter by view

        return (notify, transition, dependencies_changed)

    def update_validity(self):
        """
        Calculate the validity of the alarm considering the current time,
        the refresh rate and a previously defined delta time
        """
        if self.validity == 0:
            return self
        validity_threshold = CdbConnector.validity_threshold
        current_timestamp = int(round(time.time() * 1000))
        if current_timestamp - self.core_timestamp > validity_threshold:
            self.validity = 0
            return self
        else:
            return self

    def acknowledge(self, ack=True):
        """
        Acknowledges the Alarm if its value is SET

        Args:
            ack (optional boolean): acknowledge status to update,
            True by default

        Returns:
            boolean: the final ack status
        """
        initial_ack_state = self.ack  # counter variable
        self.ack = ack
        self.objects.update_counter_by_view_if_alarm_is_acknowledged(self, initial_ack_state)
        return self.ack

    def unacknowledge(self):
        """
        Unacknowledge the Alarm

        Returns:
            boolean: the final ack status
        """
        initial_ack_state = self.ack  # counter variable
        self.ack = False
        self.objects.update_counter_by_view_if_alarm_is_unacknowledged(self, initial_ack_state)
        return self.ack

    def shelve(self):
        """
        Shelves the Alarm

        Returns:
            int: 1 if it was shelved, 0 if not, -1 if shelving is not allowed
        """
        if not self.can_shelve:
            return -1
        if self.shelved:
            return 0
        self.shelved = True
        return 1

    def unshelve(self):
        """
        Unshelves the Alarm

        Returns:
            boolean: True if it was unshelved, False if not
        """
        if not self.shelved:
            return False
        self.shelved = False
        return True

    def is_set(self):
        """ Method to check is the alarm is set """
        return True if self.value > 0 else False

    def is_not_set(self):
        """ Method to check is the alarm is not set """
        return True if self.value == 0 else False

    def is_stored(self):
        """ Method to check is the alarm was stored in the collection """
        return self.stored


class IASValue(Alarm):
    """ IASValue from some device in the observatory. """

    def __init__(self, core_timestamp, core_id, running_id, value, mode=0,
                 validity=0, timestamps={}, state_change_timestamp=0):
        """ Constructor of the class,
        only executed when there a new instance is created.
        Receives and validates values for the attributes of the object """

        Alarm.__init__(
            self, core_timestamp, core_id, running_id, mode=mode,
            validity=validity, timestamps=timestamps,
            state_change_timestamp=state_change_timestamp
        )
        self.value = self.__check_value(value)

    def __check_value(self, value):
        """ Validates the IASValue value """
        if type(value) is not str:
            raise TypeError
        else:
            return value

    def to_dict(self):
        """ Returns a dict with all the values of the different attributes """
        return {
            'value': self.value,
            'mode': self.mode,
            'validity': self.validity,
            'core_timestamp': self.core_timestamp,
            'state_change_timestamp': self.state_change_timestamp,
            'core_id': self.core_id,
            'running_id': self.running_id,
            'timestamps': self.timestamps
        }

    def update(self, ias_value):
        """
        Updates the ias_value with attributes from another given ias_value if
        the timestamp of the given ias_value is greater than the stored ias
        value.

        Args:
            ias_value (dict): The new ias_value object

        Returns:
            string: the state of the update (not-updated, updated-equal,
            updated-different)
        """
        if ias_value.core_timestamp <= self.core_timestamp:
            logger.debug(
                'value %s was not updated (tstamp is older than the last one)',
                ias_value.core_id)
            return ('not-updated', None, False)

        if self.mode != ias_value.mode or self.value != ias_value.value or \
           (self.state_change_timestamp == 0 and ias_value.validity == 1):
            self.state_change_timestamp = ias_value.core_timestamp

        ignored_fields = \
            ['core_timestamp', 'id', 'timestamps', 'properties', 'mode',
                'validity']
        unchanged_fields = \
            ['ack', 'shelved', 'description', 'url', 'state_change_timestamp']

        notify = 'updated-equal'

        for field in ias_value.__dict__.keys():
            if field in unchanged_fields:
                continue
            old_value = getattr(self, field)
            new_value = getattr(ias_value, field)
            if (field not in ignored_fields) and old_value != new_value:
                notify = 'updated-different'
            setattr(self, field, new_value)

        return notify
