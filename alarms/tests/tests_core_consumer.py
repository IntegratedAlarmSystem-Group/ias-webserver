import datetime
import pytest
from channels.testing import WebsocketCommunicator
from alarms.collections import AlarmCollection
from ias_webserver.routing import application as ias_app
from ias_webserver.settings import PROCESS_CONNECTION_PASS


class TestCoreConsumer:
    """This class defines the test suite for the CoreConsumer"""

    def setup_method(self):
        """TestCase setup, executed before each test of the TestCase"""
        # Arrange:
        self.iasio_alarm = {
            'id': "AlarmType-ID",
            'shortDesc': "Test iasio",
            'iasType': "alarm",
            'docUrl': 'www.dummy-url.com'
        }
        self.iasio_double = {
            'id': "DoubleType-ID",
            'shortDesc': "Test iasio",
            'iasType': "double",
            'docUrl': 'www.dummy-url.com'
        }
        self.iasios = [self.iasio_alarm, self.iasio_double]
        self.ws_url = '/core/?password={}'.format(PROCESS_CONNECTION_PASS)

    @pytest.mark.asyncio
    @pytest.mark.django_db
    async def test_receive_json(self):
        """ Test if the core consumer receives the list of iasios and passes it to the AlarmCollection """
        AlarmCollection.reset(self.iasios)
        old_alarms_count = len(AlarmCollection.get_all_as_list())
        # Connect:
        communicator = WebsocketCommunicator(ias_app, self.ws_url)
        connected, subprotocol = await communicator.connect()
        assert connected, 'The communicator was not connected'
        # Arrange:
        current_time = datetime.datetime.now()
        formatted_current_time = current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        core_ids = [
            'AlarmType-ID1',
            'AlarmType-ID2',
            'AlarmType-ID3'
        ]
        msg = [
            {
                "value": "SET_MEDIUM",
                "productionTStamp": formatted_current_time,
                "sentToBsdbTStamp": formatted_current_time,
                "mode": "OPERATIONAL",   # 5: OPERATIONAL
                "iasValidity": "RELIABLE",
                "fullRunningId": "(Monitored-System-ID:MONITORED_SOFTWARE_SYSTEM)" + \
                "@(plugin-ID:PLUGIN)@(Converter-ID:CONVERTER)@(AlarmType-ID1:IASIO)",
                "valueType": "ALARM"
            },
            {
                "value": "SET_HIGH",
                "productionTStamp": formatted_current_time,
                "sentToBsdbTStamp": formatted_current_time,
                "mode": "OPERATIONAL",   # 5: OPERATIONAL
                "iasValidity": "RELIABLE",
                "fullRunningId": "(Monitored-System-ID:MONITORED_SOFTWARE_SYSTEM)" + \
                "@(plugin-ID:PLUGIN)@(Converter-ID:CONVERTER)@(AlarmType-ID2:IASIO)",
                "valueType": "ALARM"
            },
            {
                "value": "SET_MEDIUM",
                "productionTStamp": formatted_current_time,
                "sentToBsdbTStamp": formatted_current_time,
                "mode": "OPERATIONAL",   # 5: OPERATIONAL
                "iasValidity": "RELIABLE",
                "fullRunningId": "(Monitored-System-ID:MONITORED_SOFTWARE_SYSTEM)" + \
                "@(plugin-ID:PLUGIN)@(Converter-ID:CONVERTER)@(AlarmType-ID3:IASIO)",
                "valueType": "ALARM"
            },
        ]
        # Act:
        await communicator.send_json_to(msg)
        response = await communicator.receive_from()
        # Assert:
        all_alarms_list = [a.core_id for a in AlarmCollection.get_all_as_list()]
        new_alarms_count = len(all_alarms_list)
        assert response == 'Received 3 IASIOS', 'The alarms were not received'
        assert old_alarms_count + 3 == new_alarms_count, 'The Iasios shoul have been added to the AlarmCollection'
        for core_id in core_ids:
            assert core_id in all_alarms_list, 'The alarm {} is not in the collection'.format(core_id)
        # Close:
        await communicator.disconnect()
