from utils.choice_enum import ChoiceEnum
from alarms.connectors import CdbConnector
import time


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
                 validity=0, dependencies=[], properties={}, timestamps={}):

        self.core_timestamp = self.__check_int_type(core_timestamp)
        self.core_id = self.__check_str_type(core_id)
        self.running_id = self.__check_str_type(running_id)
        self.value = self.__check_value(value)
        self.mode = self.__check_mode(mode)
        self.validity = self.__check_validity(validity)
        self.dependencies = self.__check_list_type(dependencies)  # optional
        self.properties = self.__check_dict_type(properties)      # optional
        self.timestamps = self.__check_dict_type(timestamps)      # optional

    def __check_value(self, value):
        if value not in [0, 1]:
            raise TypeError
        else:
            return value

    def __check_mode(self, mode):
        if mode not in [str(x[0]) for x in OperationalMode.options()]:
            raise TypeError
        else:
            return mode

    def __check_validity(self, validity):
        if validity not in [str(x[0]) for x in Validity.options()]:
            raise TypeError
        else:
            return validity

    def __check_int_type(self, field):
        if type(field) is not int:
            raise TypeError
        else:
            return field

    def __check_str_type(self, field):
        if type(field) is not str:
            raise TypeError
        else:
            return field

    def __check_list_type(self, field):
        if type(field) is not list:
            raise TypeError
        else:
            return field

    def __check_dict_type(self, field):
        if type(field) is not dict:
            raise TypeError
        else:
            return field

    def __str__(self):
        """ Returns a string representation of the object """

        return str(self.core_id) + '=' + str(self.value)

    def to_dict(self):
        return {
            'value': self.value,
            'mode': self.mode,
            'validity': self.validity,
            'core_timestamp': self.core_timestamp,
            'core_id': self.core_id,
            'running_id': self.running_id,
            'timestamps': self.timestamps,
            'properties': self.properties,
            'dependencies': self.dependencies
        }

    def equals_except_timestamp(self, alarm):
        """
        Check if the attributes of the alarm are different to the values
        retrieved in params, the verification does not consider the
        core_timestamp value.
        """
        for key in self.__dict__.keys():
            field = key
            if field == 'core_timestamp' or field == 'id' or \
               field == 'timestamps':
                continue
            self_attribute = getattr(self, field)
            alarm_attribute = getattr(alarm, field)
            if self_attribute != alarm_attribute:
                return False
        return True

    def check_changes(self, params):
        """
        Check if the attributes of the alarm are different to the values
        retrieved in params, the verification does not consider the
        core_timestamp value.
        """
        for key, value in params.items():
            if key != 'core_timestamp' and getattr(self, key) != value:
                return True
        return False

    def update_ignoring_timestamp(self, params):
        """
        Updates the alarm with the values given in a dict,
        according to some conditions.

        Args:
            params (dict): Dictionary of values indexed by parameter names

        Returns:
            bool: True if the alarm was updated, False if not
        """
        # Update core_timestamp:
        self.core_timestamp = params['core_timestamp']

        # Update the rest of the attributes only if they are different:
        update = False
        for key, value in params.items():
            if key == 'core_timestamp':
                continue
            if getattr(self, key) != value:
                setattr(self, key, value)
                update = True

        # Save changes only if there was a different attribute (except core_id)
        if update:
            super(Alarm, self).save()
            return True
        return False

    def update_validity(self):
        """
        Calculate the validity of the alarm considering the current time,
        the refresh rate and a previously defined delta time
        """
        if self.validity == '0':
            return self
        refresh_rate = CdbConnector.refresh_rate
        tolerance = CdbConnector.tolerance
        current_timestamp = int(round(time.time() * 1000))
        if current_timestamp - self.core_timestamp > refresh_rate + tolerance:
            self.validity = '0'
            return self
        else:
            return self
