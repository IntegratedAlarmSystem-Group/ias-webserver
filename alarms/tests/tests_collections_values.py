import datetime
import time
from alarms.models import OperationalMode, Validity
from alarms.collections import AlarmCollection


class TestIasValueUpdates:
    """ This class defines the test suite for the Alarms Collection management
    of IASValues that are not of type Alarm """

    def test_create_and_update_value_to_collection(self):
        """ Test if the other types of values are added successfully to values_collection """
        # CREATE
        # Arrange:
        AlarmCollection.reset([])
        old_time = datetime.datetime.now()
        new_time = old_time + datetime.timedelta(seconds=1)
        iasio_old_time = old_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        iasio_new_time = new_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        value_old_time = int((time.mktime(old_time.timetuple()) + old_time.microsecond / 1E6) * 1000)
        value_new_time = int((time.mktime(new_time.timetuple()) + new_time.microsecond / 1E6) * 1000)
        iasio = {
            "value": "SOME_TEST_VALUE",
            "productionTStamp": iasio_old_time,
            "sentToBsdbTStamp": iasio_old_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-VALUE:IASIO)",
            "valueType": "STRING"
        }
        value = AlarmCollection.get_value('MOCK-VALUE')
        assert value is None, 'The value must not be in the collection at the beginning'
        # Act:
        AlarmCollection.add_or_update_value(iasio)
        # Assert:
        value = AlarmCollection.get_value('MOCK-VALUE')
        assert value is not None, 'The value must be in the collection'
        assert value.core_timestamp == value_old_time, 'The value must have the iasios timestamp'
        assert value.core_id == 'MOCK-VALUE', 'The value must be in the collection'
        assert value.value == 'SOME_TEST_VALUE', 'The value does not match the expected value'
        assert value.mode == OperationalMode.OPERATIONAL.value, 'Value mode does not match the Iasio mode'
        assert value.validity == Validity.RELIABLE.value, 'Value validity does not match the Iasio mode'

        # UPDATE
        # Arrange:
        iasio = {
            "value": "SOME_OTHER_TEST_VALUE",
            "productionTStamp": iasio_new_time,
            "sentToBsdbTStamp": iasio_new_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-VALUE:IASIO)",
            "valueType": "STRING"
        }
        # Act:
        AlarmCollection.add_or_update_value(iasio)
        # Assert:
        value = AlarmCollection.get_value('MOCK-VALUE')
        assert value is not None, 'The value must be in the collection'
        assert value.core_timestamp == value_new_time, 'The value timestamp should be updated'
        assert value.core_id == 'MOCK-VALUE', 'The value must be in the collection'
        assert value.value == 'SOME_OTHER_TEST_VALUE', 'The value does not match the expected value'
        assert value.mode == OperationalMode.OPERATIONAL.value, 'Value mode does not match the Iasio mode'
        assert value.validity == Validity.RELIABLE.value, 'Value validity does not match the Iasio mode'

        # SKIP UPDATE
        # Arrange:
        # iasio_time_3 = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        iasio = {
            "value": "YET_ANOTHER_TEST_VALUE",
            "productionTStamp": iasio_old_time,
            "sentToBsdbTStamp": iasio_old_time,
            "mode": "OPERATIONAL",   # 5: OPERATIONAL
            "iasValidity": "RELIABLE",
            "fullRunningId": "(Converter-ID:CONVERTER)@(MOCK-VALUE:IASIO)",
            "valueType": "STRING"
        }
        # Act:
        AlarmCollection.add_or_update_value(iasio)
        # Assert:
        value = AlarmCollection.get_value('MOCK-VALUE')
        assert value is not None, 'The value must be in the collection'
        assert value.core_timestamp == value_new_time, 'The value must not have been updated again'
        assert value.core_id == 'MOCK-VALUE', 'The value must be in the collection'
        assert value.value == 'SOME_OTHER_TEST_VALUE', 'The value does not match the expected value'
        assert value.mode == OperationalMode.OPERATIONAL.value, 'Value mode does not match the Iasio mode'
        assert value.validity == Validity.RELIABLE.value, 'Value validity does not match the Iasio mode'
