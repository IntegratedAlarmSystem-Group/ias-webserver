from factory import DjangoModelFactory, fuzzy, Sequence
from ..models import Alarm, OperationalMode, Validity
import time


class AlarmFactory(DjangoModelFactory):
    """ Factory to create random alarms based on Alarm model """
    class Meta:
        model = Alarm

    _base_core_id = 'ANTENNA_DV{0}$WVR$AMBIENT_TEMPERATURE'

    value = fuzzy.FuzzyInteger(0, 1)
    core_timestamp = int(round(time.time() * 1000))
    mode = fuzzy.FuzzyChoice([str(x[0]) for x in OperationalMode.options()])
    core_id = Sequence(
        lambda n: AlarmFactory._base_core_id.format(n)
    )
    running_id = Sequence(
        lambda n: (AlarmFactory._base_core_id + ' @ACS_NC').format(n)
    )
    validity = fuzzy.FuzzyChoice([str(x[0]) for x in Validity.options()])

    @classmethod
    def _setup_next_sequence(cls):
        try:
            return cls._meta.model.objects.latest('pk').pk + 1
        except cls._meta.model.DoesNotExist:
                return 1

    @classmethod
    def get_modified_alarm(cls, alarm):
        """ Return the alarm with the value, core_timestamp and mode modified
        randomly """

        alarm.value = (alarm.value + 1) % 2
        alarm.core_timestamp = alarm.core_timestamp + 10
        alarm.mode = \
            fuzzy.FuzzyChoice(
                [x[0] for x in OperationalMode.options() if x[0] != alarm.mode]
            )
        return alarm

    @classmethod
    def get_valid_alarm(cls, core_id=None):
        alarm = AlarmFactory.build()
        alarm.validity = '1'
        alarm.core_timestamp = int(round(time.time() * 1000))
        if core_id:
            alarm.core_id = core_id
        return alarm

    @classmethod
    def get_invalid_alarm(cls, core_id=None):
        alarm = AlarmFactory.build()
        alarm.validity = '0'
        alarm.core_timestamp = int(round(time.time() * 1000))
        if core_id:
            alarm.core_id = core_id
        return alarm
