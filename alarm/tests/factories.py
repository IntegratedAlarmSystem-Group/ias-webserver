from factory import DjangoModelFactory
from ..models import Alarm


class AlarmFactory(DjangoModelFactory):
    class Meta:
        model = Alarm

    value = 1
    core_timestamp = 10000
    mode = 1
    core_id = 'ACS_NC'
    running_id = 'ANTENNA_DV16$WVR$AMBIENT_TEMPERATURE @ACS_NC'
