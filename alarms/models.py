import time
from utils.choice_enum import ChoiceEnum
from alarms.connectors import CdbConnector


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


class Alarm:
    """ Alarm generated by some device in the observatory. """

    def __init__(self, core_timestamp, core_id, running_id, value=0, mode=0,
                 validity=0, dependencies=[], properties={}, timestamps={},
                 ack=False, shelved=False, state_change_timestamp=0):
        """ Constructor of the class,
        only executed when there a new instance is created.
        Receives and validates values for the attributes of the object """

        self.core_timestamp = self.__check_int_type(core_timestamp)
        self.core_id = self.__check_str_type(core_id)
        self.running_id = self.__check_str_type(running_id)
        self.value = self.__check_value(value)
        self.mode = self.__check_mode(mode)
        self.validity = self.__check_validity(validity)
        self.dependencies = self.__check_list_type(dependencies)  # optional
        self.properties = self.__check_dict_type(properties)      # optional
        self.timestamps = self.__check_dict_type(timestamps)      # optional
        self.ack = self.__check_ack(ack)
        self.shelved = self.__check_shelved(shelved)
        self.state_change_timestamp = self.__check_int_type(
            state_change_timestamp)

    def __check_value(self, value):
        """ Validates the Alarm value """
        if value not in [int(x[0]) for x in Value.options()]:
            raise TypeError
        else:
            return int(value)

    def __check_mode(self, mode):
        """ Validates the Alarm mode """
        if mode not in [int(x[0]) for x in OperationalMode.options()]:
            raise TypeError
        else:
            return int(mode)

    def __check_validity(self, validity):
        """ Validates the Alarm validity """
        if validity not in [int(x[0]) for x in Validity.options()]:
            raise TypeError
        else:
            return int(validity)

    def __check_int_type(self, field):
        """ Validates an integer field """
        if type(field) is not int:
            raise TypeError
        else:
            return field

    def __check_str_type(self, field):
        """ Validates a string field """
        if type(field) is not str:
            raise TypeError
        else:
            return field

    def __check_list_type(self, field):
        """ Validates a list field """
        if type(field) is not list:
            raise TypeError
        else:
            return field

    def __check_dict_type(self, field):
        """ Validates a dict field """
        if type(field) is not dict:
            raise TypeError
        else:
            return field

    def __check_ack(self, ack):
        """ Validates the Alarm shelving status.
        Which should be True if the Alarm is shelved and False if not """
        if ack not in [True, False]:
            raise TypeError
        else:
            return ack

    def __check_shelved(self, ack):
        """ Validates the Alarm ack status.
        Which should be True if the Alarm is acknowledged and False if not """
        if ack not in [True, False]:
            raise TypeError
        else:
            return ack

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
        }

    def equals_except_timestamp(self, alarm):
        """
        Check if the attributes of the alarm are different to the values
        retrieved in params, the verification does not consider the
        core_timestamp value, other timestamps values and the properties dict.
        """
        for key in self.__dict__.keys():
            field = key
            if field == 'core_timestamp' or field == 'id' or \
               field == 'timestamps' or field == 'properties':
                continue
            self_attribute = getattr(self, field)
            alarm_attribute = getattr(alarm, field)
            if self_attribute != alarm_attribute:
                return False
        return True

    def update_validity(self):
        """
        Calculate the validity of the alarm considering the current time,
        the refresh rate and a previously defined delta time
        """
        if self.validity == 0:
            return self
        refresh_rate = CdbConnector.refresh_rate
        tolerance = CdbConnector.tolerance
        current_timestamp = int(round(time.time() * 1000))
        if current_timestamp - self.core_timestamp > refresh_rate + tolerance:
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
        self.ack = ack
        return self.ack

    def shelve(self):
        """
        Shelves the Alarm

        Returns:
            boolean: True if it was shelved, False if not
        """
        if self.shelved:
            return False
        self.shelved = True
        return True

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
        return True if self.value not in Value.unset_options() else False

    def is_not_set(self):
        return True if self.value in Value.unset_options() else False
