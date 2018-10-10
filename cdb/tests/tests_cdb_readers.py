from django.test import TestCase
from cdb.readers import CdbReader
from ias_webserver.settings import BROADCAST_RATE_FACTOR


class CdbReaderTestCase(TestCase):

    def test_read_ias(self):
        """ Test if we can read ths IAS json file from the CDB """
        # Act:
        ias_data = CdbReader.read_ias()
        # Asserts:
        expected_data = {
            'logLevel': 'INFO',
            'refreshRate': '3',
            'tolerance': '1',
            'hbFrequency': '5',
            'broadcastFactor': str(BROADCAST_RATE_FACTOR),
            'props': [
                {'name': 'Prop1-Name', 'value': 'The value of P1'},
                {'name': 'Prop2-Name', 'value': 'The value of P2'}
            ]
        }
        self.assertEqual(
            ias_data, expected_data,
            'The data obtained with the read_data method is not the expected'
        )

    def test_read_iasios_basefile(self):
        """ Test if we can read the IASIOS json file from the CDB """
        # Act:
        iasios_data = CdbReader.read_iasios_file()
        # Asserts:
        expected_entry = {
            "id": "IASIO-DUMMY_DOUBLE_1",
            "shortDesc": "Dummy Iasio of tyoe DOUBLE",
            "iasType": "DOUBLE",
            "docUrl": "http://www.alma.cl"
        }
        self.assertTrue(
            expected_entry in iasios_data,
            'The data obtained with the read_data method is not the expected'
        )

    def test_read_dasu_outputs(self):
        """ Test if we can read the iasios that are actually output of DASUs
        in the CDB """
        # Act:
        dasu_outputs = CdbReader.read_dasus_outputs()
        # Asserts:
        expected_data = [
            "IASIO_DUMMY_ALARM_1",
            "IASIO_DUMMY_ALARM_2",
            "IASIO_DUMMY_ALARM_8",
            "IASIO_DUMMY_TEMPLATED_1",
        ]
        self.assertEqual(
            sorted(dasu_outputs), sorted(expected_data),
            'The data obtained is not the expected'
        )

    def test_read_alarm_iasios(self):
        """ Test if we can read the validated IASIOS that are actual outputs
        of DASUSs in the CDB """
        # Act:
        iasios_data = CdbReader.read_alarm_iasios()
        # Asserts:
        expected_data = [
            {
                "id": "IASIO_DUMMY_ALARM_1",
                "shortDesc": "Dummy Iasio of tyoe ALARM",
                "iasType": "ALARM",
                "docUrl": "http://www.alma.cl"
            },
            {
                "id": "IASIO_DUMMY_ALARM_2",
                "shortDesc": "Dummy Iasio of tyoe ALARM",
                "iasType": "ALARM",
                "docUrl": "http://www.alma.cl"
            },
            {
                "id": "IASIO_DUMMY_ALARM_8",
                "shortDesc": "Dummy Iasio of tyoe ALARM",
                "iasType": "ALARM",
                "docUrl": "http://www.alma.cl"
            },
            {
                "id": "IASIO_DUMMY_TEMPLATED_1 instance 3",
                "shortDesc": "Dummy teplated Iasio 1",
                "iasType": "ALARM",
                "templateId": "template-ID1"
            },
            {
                "id": "IASIO_DUMMY_TEMPLATED_1 instance 4",
                "shortDesc": "Dummy teplated Iasio 1",
                "iasType": "ALARM",
                "templateId": "template-ID1"
            },
            {
                "id": "IASIO_DUMMY_TEMPLATED_1 instance 5",
                "shortDesc": "Dummy teplated Iasio 1",
                "iasType": "ALARM",
                "templateId": "template-ID1"
            },
            {
                "id": "IASIO_DUMMY_TEMPLATED_1 instance 6",
                "shortDesc": "Dummy teplated Iasio 1",
                "iasType": "ALARM",
                "templateId": "template-ID1"
            },
            {
                "id": "IASIO_DUMMY_TEMPLATED_1 instance 7",
                "shortDesc": "Dummy teplated Iasio 1",
                "iasType": "ALARM",
                "templateId": "template-ID1"
            },
            {
                "id": "IASIO_DUMMY_TEMPLATED_1 instance 8",
                "shortDesc": "Dummy teplated Iasio 1",
                "iasType": "ALARM",
                "templateId": "template-ID1"
            },
        ]
        self.assertEqual(
            iasios_data, expected_data,
            'The data obtained is not the expected'
        )
