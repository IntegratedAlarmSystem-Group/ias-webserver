from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from ias_webserver.settings import BROADCAST_RATE_FACTOR
from cdb.models import Ias, Iasio


class CdbApiTestCase(TestCase):
    """Test suite for the api views."""

    def setUp(self):
        # Arrange:
        """Define the test suite setup"""
        self.ias = Ias(id=1, log_level='debug', refresh_rate=3, tolerance=1)
        self.ias.save()

        self.iasio1 = Iasio(io_id='Test-ID1',
                            short_desc='Test iasio',
                            ias_type='double')
        self.iasio2 = Iasio(io_id='Test-ID2',
                            short_desc='Test iasio',
                            ias_type='alarm')
        self.iasio3 = Iasio(io_id='Test-ID3',
                            short_desc='Test iasio',
                            ias_type='alarm')
        self.iasio1.save()
        self.iasio2.save()
        self.iasio3.save()

        self.client = APIClient()

    def tearDown(self):
        """TestCase teardown"""
        Iasio.objects.all().delete()
        Ias.objects.all().delete()

    def test_api_can_retrieve_ias(self):
        """ Test that the api can retrieve an Ias """
        # Arrange:
        expected_ias_data = self.ias.get_data()
        expected_ias_data['broadcast_factor'] = BROADCAST_RATE_FACTOR
        # Act:
        url = reverse('ias-detail', kwargs={'pk': self.ias.id})
        self.response = self.client.get(url, format="json")
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the ias'
        )
        retrieved_ias_data = self.response.data
        retrieved_ias_data.pop('id', None)
        self.assertEqual(
            retrieved_ias_data,
            expected_ias_data,
            'The retrieved ias does not match the expected'
        )

    def test_api_can_retrieve_iasio(self):
        """ Test that the api can retrieve an Iasio """
        # Arrange:
        expected_iasio_data = self.iasio1.get_data()
        # Act:
        url = reverse('iasio-detail', kwargs={'pk': self.iasio1.io_id})
        self.response = self.client.get(url, format="json")
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the iasio'
        )
        retrieved_iasio_data = self.response.data
        retrieved_iasio_data.pop('id', None)
        self.assertEqual(
            retrieved_iasio_data,
            expected_iasio_data,
            'The retrieved iasio does not match the expected'
        )

    def test_api_can_list_iasios(self):
        """Test that the api can list the Iasios"""
        iasios = [self.iasio1, self.iasio2, self.iasio3]
        expected_iasios_data = [iasio.get_data() for iasio in iasios]
        # Act:
        url = reverse('iasio-list')
        self.response = self.client.get(url, format="json")
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the iasios'
        )
        retrieved_iasios_data = self.response.data
        for data in retrieved_iasios_data:
            data.pop('id', None)
        self.assertEqual(
            retrieved_iasios_data,
            expected_iasios_data,
            'The retrieved iasios do not match the expected ones'
        )

    def test_api_can_list_iasios_of_type_alarm(self):
        """ Test that the api can list the Iasios with type Alarm """
        iasios = [self.iasio2, self.iasio3]
        expected_iasios_data = [iasio.get_data() for iasio in iasios]
        # Act:
        url = reverse('iasio-filtered-by-alarm')
        self.response = self.client.get(url, format="json")
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the iasios'
        )
        retrieved_iasios_data = self.response.data
        for data in retrieved_iasios_data:
            data.pop('id', None)
        self.assertEqual(
            retrieved_iasios_data,
            expected_iasios_data,
            'The retrieved iasios do not match the expected ones'
        )
