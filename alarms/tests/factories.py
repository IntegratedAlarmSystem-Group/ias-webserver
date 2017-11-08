from factory import DjangoModelFactory, fuzzy, Sequence
from ..models import Alarm, OperationalMode


class AlarmFactory(DjangoModelFactory):
    class Meta:
        model = Alarm

    value = fuzzy.FuzzyInteger(0, 1)
    core_timestamp = fuzzy.FuzzyInteger(0, 100000)
    mode = str(fuzzy.FuzzyChoice([x[0] for x in OperationalMode.options()]))
    core_id = Sequence(
        lambda n: 'ANTENNA_DV{0}$WVR$AMBIENT_TEMPERATURE'.format(n)
    )
    running_id = str(core_id) + ' @ACS_NC'

    @classmethod
    def _setup_next_sequence(cls):
        try:
            return cls._meta.model.objects.latest('pk').pk + 1
        except cls._meta.model.DoesNotExist:
                return 1

    @classmethod
    def get_modified_alarm(cls, alarm):
        alarm.value = (alarm.value + 1) % 2
        alarm.core_timestamp = alarm.core_timestamp + 10
        alarm.mode = \
            str(fuzzy.FuzzyChoice(
                [x[0] for x in OperationalMode.options() if x[0] != alarm.mode]
            ))
        return alarm
