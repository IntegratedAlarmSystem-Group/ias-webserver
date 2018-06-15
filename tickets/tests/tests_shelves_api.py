import mock
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from tickets.models import ShelveRegistry, ShelveRegistryStatus
from tickets.serializers import ShelveRegistrySerializer


class ShelveRegistrysApiTestCase(TestCase):
    """Test suite for the registries api views."""

    def setUp(self):
        # Arrange:
        """Define the test suite setup"""
        self.message = 'Shelved because of reasons'
        self.registry_shelved = ShelveRegistry(
            alarm_id='alarm_1',
            message=self.message
        )
        self.registry_shelved.save()

        self.registry_unshelved = ShelveRegistry(
            alarm_id='alarm_1',
            message=self.message
        )
        self.registry_unshelved.save()
        self.registry_unshelved.unshelve()

        self.registry_other = ShelveRegistry(
            alarm_id='alarm_2',
            message=self.message
        )
        self.registry_other.save()
        self.client = APIClient()

    def test_api_can_create_registry(self):
        """ Test that the api can create a registry """
        # Arrange
        new_reg_data = {
            'alarm_id': 'alarm_3',
            'message': self.message
        }
        # Act:
        url = reverse('shelveregistry-list')
        self.response = self.client.post(url, new_reg_data, format='json')
        # Assert:
        expected_reg = ShelveRegistry.objects.get(
            alarm_id=new_reg_data['alarm_id']
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_201_CREATED,
            'The server did not create the registry'
        )
        self.assertEqual(
            self.response.data,
            ShelveRegistrySerializer(expected_reg).data
        )

    def test_api_cannot_create_registry_with_no_message(self):
        """ Test that the api cannot create a registry without a message """
        # Arrange:
        new_reg_data = {
            'alarm_id': 'alarm_3'
        }
        # Act:
        url = reverse('shelveregistry-list')
        self.response = self.client.post(url, new_reg_data, format='json')
        # Assert:
        expected_reg = list(
            ShelveRegistry.objects.filter(alarm_id=new_reg_data['alarm_id'])
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'The server created the registry'
        )
        self.assertEqual(
            expected_reg,
            [],
            'The registry was created'
        )

    def test_api_can_retrieve_registry(self):
        """ Test that the api can retrieve a registry """
        # Arrange:
        expected_reg = ShelveRegistry.objects.get(pk=self.registry_shelved.pk)
        # Act:
        url = reverse(
            'shelveregistry-detail',
            kwargs={'pk': self.registry_shelved.pk}
        )
        self.response = self.client.get(url, format='json')
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The server did not retrieve the registry'
        )
        self.assertEqual(
            self.response.data,
            ShelveRegistrySerializer(expected_reg).data
        )

    def test_api_can_list_registries(self):
        """Test that the api can list the ShelveRegistries"""
        registries = [
            self.registry_shelved,
            self.registry_unshelved,
            self.registry_other
        ]
        expected_registries_data = [
            ShelveRegistrySerializer(t).data for t in registries]
        # Act:
        url = reverse('shelveregistry-list')
        self.response = self.client.get(url, format="json")
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the registries'
        )
        retrieved_registries_data = self.response.data
        self.assertEqual(
            retrieved_registries_data,
            expected_registries_data,
            'The retrieved registries do not match the expected ones'
        )

    # def test_api_can_filter_registries_by_alarm_and_status(self):
    #     """Test that the api can list the ShelveRegistrys filtered by alarm id
    #     and status"""
    #     expected_registries_data = [ShelveRegistrySerializer(self.registry_shelved).data]
    #     # Act:
    #     url = reverse('registry-filters')
    #     data = {
    #         'alarm_id': 'alarm_1',
    #         'status': ShelveRegistryStatus.get_choices_by_name()['UNACK']
    #     }
    #     self.response = self.client.get(url, data, format="json")
    #     # Assert:
    #     self.assertEqual(
    #         self.response.status_code,
    #         status.HTTP_200_OK,
    #         'The Server did not retrieve the filtered registries'
    #     )
    #     retrieved_registries_data = self.response.data
    #     self.assertEqual(
    #         retrieved_registries_data,
    #         expected_registries_data,
    #         'The retrieved filtered registries do not match the expected ones'
    #     )
    #
    # def test_api_can_filter_registries_by_alarm(self):
    #     """Test that the api can list the ShelveRegistrys filtered by alarm id"""
    #     registries = [self.registry_shelved, self.registry_unshelved]
    #     expected_registries_data = [ShelveRegistrySerializer(t).data for t in registries]
    #     # Act:
    #     url = reverse('registry-filters')
    #     data = {
    #         'alarm_id': 'alarm_1'
    #     }
    #     self.response = self.client.get(url, data, format="json")
    #     # Assert:
    #     self.assertEqual(
    #         self.response.status_code,
    #         status.HTTP_200_OK,
    #         'The Server did not retrieve the filtered registries'
    #     )
    #     retrieved_registries_data = self.response.data
    #     self.assertEqual(
    #         retrieved_registries_data,
    #         expected_registries_data,
    #         'The retrieved filtered registries do not match the expected ones'
    #     )
    #
    # def test_api_can_filter_registries_by_status(self):
    #     """Test that the api can list the ShelveRegistrys filtered by status"""
    #     registries = [self.registry_shelved, self.registry_other]
    #     expected_registries_data = [ShelveRegistrySerializer(t).data for t in registries]
    #     # Act:
    #     url = reverse('registry-filters')
    #     data = {
    #         'status': ShelveRegistryStatus.get_choices_by_name()['UNACK']
    #     }
    #     self.response = self.client.get(url, data, format="json")
    #     # Assert:
    #     self.assertEqual(
    #         self.response.status_code,
    #         status.HTTP_200_OK,
    #         'The Server did not retrieve the filtered registries'
    #     )
    #     retrieved_registries_data = self.response.data
    #     self.assertEqual(
    #         retrieved_registries_data,
    #         expected_registries_data,
    #         'The retrieved filtered registries do not match the expected ones'
    #     )
    #
    # @mock.patch('registries.connectors.AlarmConnector.acknowledge_alarms')
    # def test_api_can_acknowledge_a_registry(
    #     self, AlarmConnector_acknowledge_alarms
    # ):
    #     """Test that the api can ack an unacknowledged registry"""
    #     # Act:
    #     url = reverse(
    #         'registry-acknowledge', kwargs={'pk': self.registry_shelved.pk})
    #     data = {
    #         'message': 'The registry was acknowledged'
    #     }
    #     self.response = self.client.put(url, data, format="json")
    #     # Assert:
    #     self.assertEqual(
    #         self.response.status_code,
    #         status.HTTP_200_OK,
    #         'The Server did not retrieve the filtered registries'
    #     )
    #     acknowledged_registry = ShelveRegistry.objects.get(pk=self.registry_shelved.pk)
    #     self.assertEqual(
    #         acknowledged_registry.status,
    #         int(ShelveRegistryStatus.get_choices_by_name()['ACK']),
    #         'The acknowledged registry was not correctly acknowledged'
    #     )
    #     self.assertEqual(
    #         acknowledged_registry.message, data['message'],
    #         'The acknowledged registry message was not correctly recorded'
    #     )
    #     self.assertNotEqual(
    #         acknowledged_registry.acknowledged_at, None,
    #         'The acknowledged registry datetime was not correctly recorded'
    #     )
    #     self.assertEqual(
    #         AlarmConnector_acknowledge_alarms.call_count, 1,
    #         'AlarmConnector.acknowledge_alarms should have been called'
    #     )
    #     AlarmConnector_acknowledge_alarms.assert_called_with(
    #         [self.registry_shelved.alarm_id]
    #     )
    #
    # def test_api_can_not_acknowledge_a_registry_without_message(self):
    #     """Test that the api can not ack an unacknowledged registry with an empty
    #     message"""
    #     # Act:
    #     url = reverse(
    #         'registry-acknowledge', kwargs={'pk': self.registry_shelved.pk})
    #     data = {
    #         'message': ' '
    #     }
    #     self.response = self.client.put(url, data, format="json")
    #     # Assert:
    #     self.assertEqual(
    #         self.response.status_code,
    #         status.HTTP_400_BAD_REQUEST,
    #         'The Server must not retrieve the filtered registries without a valid \
    #         message'
    #     )
    #     acknowledged_registry = ShelveRegistry.objects.get(pk=self.registry_shelved.pk)
    #     self.assertEqual(
    #         acknowledged_registry.status,
    #         int(ShelveRegistryStatus.get_choices_by_name()['UNACK']),
    #         'The registry must not be acknowledged'
    #     )
    #     self.assertEqual(
    #         acknowledged_registry.message, None,
    #         'The registry must not be recorded with an invalid message'
    #     )
    #     self.assertEqual(
    #         acknowledged_registry.acknowledged_at, None,
    #         'The acknowledged_at datetime must not be updated'
    #     )
    #
    # @mock.patch('registries.connectors.AlarmConnector.acknowledge_alarms')
    # def test_api_can_acknowledge_multiple_registries(
    #     self, AlarmConnector_acknowledge_alarms
    # ):
    #     """Test that the api can acknowledge multiple unacknowledged registries"""
    #     # Act:
    #     url = reverse('registry-acknowledge-many')
    #     alarms_to_ack = ['alarm_1', 'alarm_2']
    #     data = {
    #         'alarms_ids': alarms_to_ack,
    #         'message': 'The registry was acknowledged'
    #     }
    #     self.response = self.client.put(url, data, format="json")
    #     # Assert:
    #     print(self.response.data)
    #     self.assertEqual(
    #         self.response.status_code,
    #         status.HTTP_200_OK,
    #         'The status of the response is incorrect'
    #     )
    #     self.assertEqual(
    #         self.response.data,
    #         alarms_to_ack,
    #         'The response is not as expected'
    #     )
    #     acknowledged_registries = [
    #         ShelveRegistry.objects.get(pk=self.registry_shelved.pk),
    #         ShelveRegistry.objects.get(pk=self.registry_other.pk)
    #     ]
    #     expected_status = int(ShelveRegistryStatus.get_choices_by_name()['ACK'])
    #     self.assertTrue(
    #         acknowledged_registries[0].status == expected_status and
    #         acknowledged_registries[1].status == expected_status,
    #         'The registries was not correctly acknowledged'
    #     )
    #     self.assertEqual(
    #         acknowledged_registries[0].message, data['message'],
    #         'The first registry message was not correctly recorded'
    #     )
    #     self.assertEqual(
    #         acknowledged_registries[1].message, data['message'],
    #         'The second registry message was not correctly recorded'
    #     )
    #     self.assertEqual(
    #         AlarmConnector_acknowledge_alarms.call_count, 1,
    #         'AlarmConnector.acknowledge_alarms should have been called'
    #     )
    #     AlarmConnector_acknowledge_alarms.assert_called_with(alarms_to_ack)
