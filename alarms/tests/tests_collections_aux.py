import datetime
import time
import pytest
from freezegun import freeze_time
from alarms.models import Alarm, Value, IASValue, OperationalMode, Validity
from alarms.tests.factories import AlarmFactory
from alarms.collections import AlarmCollection
from alarms.connectors import CdbConnector, TicketConnector, PanelsConnector


class TestAlarmsCollectionAux:
    """ This class defines the test suite for the Alarms Collection auxiliary functions """

    def test_get_core_id_from(self):
        """Test if the core_id value is extracted correctly from the full
        running id field"""
        # Arrange:
        full_running_id = '(Monitored-System-ID:MONITORED_SOFTWARE_SYSTEM)@' +\
                          '(plugin-ID:PLUGIN)@(Converter-ID:CONVERTER)@' +\
                          '(AlarmType-ID:IASIO)'
        # Act:
        id = AlarmCollection._get_core_id_from(full_running_id)
        # Assert:
        assert id == 'AlarmType-ID', \
            'The core_id was not extracted correctly from the running_id'

    def test_get_templated_core_id_from(self):
        """Test if the core_id corresponding to a templated alarm is extracted
        and cleaned correctly from running id field"""
        # Arrange:
        full_running_id = '(Monitored-System-ID:MONITORED_SOFTWARE_SYSTEM)@' +\
                          '(plugin-ID:PLUGIN)@(Converter-ID:CONVERTER)@' +\
                          '(AlarmType-Ant[!#66!]:IASIO)'
        # Act:
        id = AlarmCollection._get_core_id_from(full_running_id)
        # Assert:
        assert id == 'AlarmType-Ant instance 66', \
            'The core_id was not extracted correctly from the running_id'

    def test_create_alarm_from_cdb_iasio(self):
        """Test the behaviour of the function tohat creates Alarms from IASIOS in the CDB"""
        # Arrange:
        iasio = {
            "id": "IASIO-DUMMY_DOUBLE_1",
            "shortDesc": "Dummy teplated Iasio 1",
            "docUrl": "www.alma.cl",
            "iasType": "ALARM",
            "templateId": "template-ID1",
            "canShelve": "true",
            "sound": "TYPE1"
        }
        AlarmCollection.alarms_views_dict = {}
        # Act:
        alarm = AlarmCollection._create_alarm_from_cdb_iasio(iasio)
        # Assert:
        assert alarm.core_id == 'IASIO-DUMMY_DOUBLE_1', 'The alarm core_id is not as expected'
        assert alarm.running_id == '(IASIO-DUMMY_DOUBLE_1:IASIO)', 'The alarm running_id is not as expected'
        assert alarm.value == Value.CLEARED.value, 'The alarm value is not as expected'
        assert alarm.mode == OperationalMode.UNKNOWN.value, 'The alarm mode is not as expected'
        assert alarm.validity == Validity.UNRELIABLE.value, 'The alarm validity is not as expected'
        assert alarm.description == 'Dummy teplated Iasio 1', 'The alarm description is not as expected'
        assert alarm.url == 'www.alma.cl', 'The alarm url is not as expected'
        assert alarm.can_shelve is True, 'The alarm can_shelve is not as expected'
        assert alarm.ack is False, 'The alarm ack is not as expected'
        assert alarm.shelved is False, 'The alarm shelved is not as expected'
        assert alarm.stored is False, 'The alarm stored is not as expected'
        assert alarm.timestamps == {}, 'The alarm timestamps is not as expected'
        assert alarm.properties == {}, 'The alarm properties is not as expected'
        assert alarm.dependencies == [], 'The alarm dependencies is not as expected'
        assert alarm.state_change_timestamp == 0, 'The alarm state_change_timestamp is not as expected'
        assert alarm.value_change_timestamp == 0, 'The alarm value_change_timestamp is not as expected'
