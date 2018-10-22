import random
from alarms.models import Alarm, OperationalMode, Validity, Value
import time


class AlarmFactory:
    """ Factory to create random alarms based on Alarm model.
    Consider that the alarms are not saved in any database """

    sequence = 0

    _base_core_id = 'ANTENNA_DV{0}$WVR$AMBIENT_TEMPERATURE'
    """
    Private parameter that defines the base of the default core ID that
    will be used for all the Alarms to be created by the factory,
    unless another core ID is specified
    """
    core_timestamp = int(round(time.time() * 1000))
    """ Core timestamp of the Alarm to be created """

    value = random.choice([int(x[0]) for x in Value.options()])
    """ Value of the Alarm to be created """

    mode = random.choice([int(x[0]) for x in OperationalMode.options()])
    """ Operational Mode of the Alarm to be created """

    validity = random.choice([int(x[0]) for x in Validity.options()])
    """ Validity of the Alarm to be created """

    ack = False
    """ Acknowledgement status of the Alarm """

    shelved = False
    """ Shelved status of the Alarm """

    @classmethod
    def build(self):
        core_id = self._base_core_id.format(self.sequence)
        alarm = Alarm(value=self.value,
                      core_timestamp=self.core_timestamp,
                      state_change_timestamp=self.core_timestamp,
                      mode=self.mode,
                      core_id=core_id,
                      running_id=core_id + '@ACS_NC',
                      validity=self.validity)
        AlarmFactory.sequence = AlarmFactory.sequence + 1
        return alarm

    @classmethod
    def get_alarm_with_all_optional_fields(self):
        """ Return a valid alarm with values for all the optional fields """
        alarm = AlarmFactory.build()
        alarm.dependencies = [
            "DEP1", "DEP2", "DEP3"
        ]
        alarm.properties = {"prop1": "value1", "prop2": "value2"}
        alarm.timestamps = {"sentToBsdbTStamp": "2018-03-07T13:08:43",
                            "dasuProductionTStamp": "2018-03-07T13:08:43"}
        return alarm

    @classmethod
    def get_modified_alarm(cls, alarm):
        """ Return the alarm with the value, core_timestamp and mode modified
        randomly """

        alarm.value = (alarm.value + 1) % 2
        alarm.core_timestamp = alarm.core_timestamp + 10
        alarm.mode = random.choice(
            [int(x[0]) for x in OperationalMode.options()
                if x[0] != alarm.mode]
        )
        return alarm

    @classmethod
    def get_valid_alarm(cls, core_id=None):
        """ Returns a valid Alarm

        Args:
            core_id (string): optional argument to specify the core_id
            of the Alarm to be returned

        Returns:
            alarm (Alarm): an instance of a valid Alarm
        """
        alarm = AlarmFactory.build()
        alarm.validity = 1
        alarm.core_timestamp = int(round(time.time() * 1000))
        if core_id:
            alarm.core_id = core_id
        return alarm

    @classmethod
    def get_invalid_alarm(cls, core_id=None):
        """ Returns a invalid Alarm

        Args:
            core_id (string): optional argument to specify the core_id
            of the Alarm to be returned

        Returns:
            alarm (Alarm): an instance of a invalid Alarm
        """
        alarm = AlarmFactory.build()
        alarm.validity = 0
        alarm.core_timestamp = int(round(time.time() * 1000))
        if core_id:
            alarm.core_id = core_id
        return alarm
