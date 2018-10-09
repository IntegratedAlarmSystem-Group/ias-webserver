from django.test import TestCase
from rest_framework import status
from django.urls import reverse
from cdb.readers import IasReader


class CdbApiTestCase(TestCase):
    """Test suite for the api views."""

    def test_api_can_list_ias(self):
        """ Test that the api can retrieve an Ias """
        # Arrange:
        expected_ias_data = IasReader.read_ias()
        # Act:
        url = reverse('ias')
        self.response = self.client.get(url, format="json")
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the ias'
        )
        retrieved_ias_data = self.response.data
        self.assertEqual(
            retrieved_ias_data,
            expected_ias_data,
            'The retrieved ias does not match the expected'
        )

    def test_api_can_get_ias(self):
        """ Test that the api can retrieve an Ias """
        # Arrange:
        expected_ias_data = IasReader.read_ias()
        # Act:
        url = reverse('ias')
        self.response = self.client.get(url, kwargs={'pk': 0}, format="json")
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the ias'
        )
        retrieved_ias_data = self.response.data
        self.assertEqual(
            retrieved_ias_data,
            expected_ias_data,
            'The retrieved ias does not match the expected'
        )
