from factory import DjangoModelFactory, fuzzy, Sequence
from ..models import Alarm, OperationalMode, Validity
import time


class AlarmFactory(DjangoModelFactory):
    """ Factory to create random alarms based on Alarm model """

    class Meta:
        """ Meta class of the AlarmFactory """

        model = Alarm
        """ Class from which this factory can create instances """

    _base_core_id = 'ANTENNA_DV{0}$WVR$AMBIENT_TEMPERATURE'
    """
    Private parameter that defines the base of the default core ID that
    will be used for all the Alarms to be created by the factory,
    unless another core ID is specified
    """

    value = fuzzy.FuzzyInteger(0, 1)
    """ Value of the Alarm to be created """

    core_timestamp = int(round(time.time() * 1000))
    """ Core timestamp of the Alarm to be created """

    mode = fuzzy.FuzzyChoice([str(x[0]) for x in OperationalMode.options()])
    """ Operational Mode of the Alarm to be created """

    core_id = Sequence(
        lambda n: AlarmFactory._base_core_id.format(n)
    )
    """ Core ID of the Alarm to be created """

    running_id = Sequence(
        lambda n: (AlarmFactory._base_core_id + ' @ACS_NC').format(n)
    )
    """ Running ID of the Alarm to be created """

    validity = fuzzy.FuzzyChoice([str(x[0]) for x in Validity.options()])
    """ Validity of the Alarm to be created """

    @classmethod
    def _setup_next_sequence(cls):
        """
        Private method that increments the numbering used for the
        next instance to be created by the factory
        """
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
        """ Returns a valid Alarm

        Args:
            core_id (string): optional argument to specify the core_id
            of the Alarm to be returned

        Returns:
            alarm (Alarm): an instance of a valid Alarm
        """
        alarm = AlarmFactory.build()
        alarm.validity = '1'
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
        alarm.validity = '0'
        alarm.core_timestamp = int(round(time.time() * 1000))
        if core_id:
            alarm.core_id = core_id
        return alarm
