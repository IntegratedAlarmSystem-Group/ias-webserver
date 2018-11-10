import mock
import datetime
from freezegun import freeze_time
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
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
        self.registry_1 = ShelveRegistry.objects.create(
            alarm_id='alarm_1',
            message=self.message,
            timeout=datetime.timedelta(hours=2),
            user='testuser'
        )
        self.registry_2 = ShelveRegistry.objects.create(
            alarm_id='alarm_2',
            message=self.message,
            timeout=datetime.timedelta(hours=2),
            user='testuser'
        )
        self.registry_2.unshelve()
        self.registry_3 = ShelveRegistry.objects.create(
            alarm_id='alarm_3',
            message=self.message,
            timeout=datetime.timedelta(hours=2),
            user='testuser'
        )
        self.client = APIClient()

    # ******* CREATE
    @mock.patch('tickets.connectors.AlarmConnector.shelve_alarm')
    def test_api_can_create_registry(self, AlarmConnector_shelve_alarm):
        """ Test that the api can create a registry """
        # Arrange
        new_reg_data = {
            'alarm_id': 'alarm_4',
            'message': self.message,
            'timeout': '3:16:13',
            'user': 'testuser'
        }
        AlarmConnector_shelve_alarm.return_value = 1
        # Act:
        url = reverse('shelveregistry-list')
        self.response = self.client.post(url, new_reg_data, format='json')
        # Assert:
        created_reg = ShelveRegistry.objects.get(
            alarm_id=new_reg_data['alarm_id']
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_201_CREATED,
            'The server did not create the registry'
        )
        retrieved_data = {
            'alarm_id': created_reg.alarm_id,
            'message': created_reg.message,
            'timeout': str(created_reg.timeout),
            'user': created_reg.user
        }
        self.assertEqual(
            retrieved_data,
            new_reg_data,
            'The created registry does not match the data sent in the request'
        )
        self.assertEqual(
            self.response.data,
            ShelveRegistrySerializer(created_reg).data,
            'The response does not match the created registry'
        )
        self.assertTrue(
            AlarmConnector_shelve_alarm.called,
            'The alarm connector shelve method should have been called'
        )

    @mock.patch('tickets.connectors.AlarmConnector.shelve_alarm')
    @mock.patch('tickets.connectors.AlarmConnector.unshelve_alarms')
    def test_api_cannot_create_registry_with_no_message(
            self, AlarmConnector_shelve_alarm, AlarmConnector_unshelve_alarms
    ):
        """ Test that the api cannot create a registry without a message """
        # Arrange:
        new_reg_data = {
            'alarm_id': 'alarm_4',
            'user': 'testuser'
        }
        AlarmConnector_shelve_alarm.return_value = 1
        # Act:
        url = reverse('shelveregistry-list')
        self.response = self.client.post(url, new_reg_data, format='json')
        # Assert:
        created_reg = list(
            ShelveRegistry.objects.filter(alarm_id=new_reg_data['alarm_id'])
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'The server created the registry'
        )
        self.assertEqual(
            created_reg,
            [],
            'The registry was created'
        )
        self.assertTrue(
            AlarmConnector_unshelve_alarms.called,
            'The alarm connector unshelve method should have been called'
        )

    @mock.patch('tickets.connectors.AlarmConnector.shelve_alarm')
    def test_api_cannot_create_registry_for_non_shelvable_alarm(
        self, AlarmConnector_shelve_alarm
    ):
        """ Test that the api can create a registry """
        # Arrange
        new_reg_data = {
            'alarm_id': 'alarm_4',
            'message': self.message,
            'timeout': '3:16:13',
            'user': 'testuser'
        }
        AlarmConnector_shelve_alarm.return_value = -1
        # Act:
        url = reverse('shelveregistry-list')
        self.response = self.client.post(url, new_reg_data, format='json')
        # Assert:
        created_reg = ShelveRegistry.objects.filter(
            alarm_id=new_reg_data['alarm_id']
        ).first()
        self.assertEqual(
            self.response.status_code,
            status.HTTP_403_FORBIDDEN,
            'The server did not forbid to create the registry'
        )
        self.assertEqual(
            created_reg,
            None,
            'The registry was created'
        )
        self.assertTrue(
            AlarmConnector_shelve_alarm.called,
            'The alarm connector shelve method should have been called'
        )

    @mock.patch('tickets.connectors.AlarmConnector.shelve_alarm')
    def test_api_cannot_create_registry_for_already_shelved_alarm(
        self, AlarmConnector_shelve_alarm
    ):
        """ Test that the api can create a registry """
        # Arrange
        new_reg_data = {
            'alarm_id': 'alarm_4',
            'message': self.message,
            'timeout': '3:16:13',
            'user': 'testuser'
        }
        AlarmConnector_shelve_alarm.return_value = 0
        # Act:
        url = reverse('shelveregistry-list')
        self.response = self.client.post(url, new_reg_data, format='json')
        # Assert:
        created_reg = ShelveRegistry.objects.filter(
            alarm_id=new_reg_data['alarm_id']
        ).first()
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The server re-shelved the alarm'
        )
        self.assertEqual(
            created_reg,
            None,
            'A new registry was created'
        )
        self.assertTrue(
            AlarmConnector_shelve_alarm.called,
            'The alarm connector shelve method should have been called'
        )

    # ******* RETRIEVE
    def test_api_can_retrieve_registry(self):
        """ Test that the api can retrieve a registry """
        # Arrange:
        expected_reg = ShelveRegistry.objects.get(pk=self.registry_1.pk)
        # Act:
        url = reverse(
            'shelveregistry-detail',
            kwargs={'pk': self.registry_1.pk}
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
            self.registry_1,
            self.registry_2,
            self.registry_3
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

    # ******* UPDATE
    def test_api_can_update_registry(self):
        """ Test that the api can update a registry """
        # Arrange
        new_reg_data = {
            'alarm_id': self.registry_1.alarm_id,
            'message': 'Another message',
            'user': self.registry_1.user
        }
        # Act:
        url = reverse(
            'shelveregistry-detail',
            kwargs={'pk': self.registry_1.pk}
        )
        self.response = self.client.put(url, new_reg_data, format='json')
        # Assert:
        updated_reg = ShelveRegistry.objects.get(
            alarm_id=self.registry_1.alarm_id
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The server did not update the registry'
        )
        self.assertEqual(
            {'alarm_id': updated_reg.alarm_id,
             'message': updated_reg.message,
             'user': updated_reg.user},
            new_reg_data,
            'The updated registry does not match the data sent in the request'
        )
        self.assertEqual(
            self.response.data,
            ShelveRegistrySerializer(updated_reg).data,
            'The response does not match the updated registry'
        )

    def test_api_cannot_update_registry_to_have_no_message(self):
        """ Test that the api cannot update a registry and leave it without
        a message """
        # Arrange
        new_reg_data = {
            'alarm_id': self.registry_1.alarm_id,
            'message': '',
            'user': self.registry_1.user
        }
        # Act:
        url = reverse(
            'shelveregistry-detail',
            kwargs={'pk': self.registry_1.pk}
        )
        self.response = self.client.put(url, new_reg_data, format='json')
        # Assert:
        updated_reg = ShelveRegistry.objects.get(
            alarm_id=self.registry_1.alarm_id
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_400_BAD_REQUEST,
            'The server updated the registry'
        )
        self.assertEqual(
            {
                'alarm_id': updated_reg.alarm_id,
                'message': updated_reg.message,
                'user': updated_reg.user
            },
            {
                'alarm_id': self.registry_1.alarm_id,
                'message': self.registry_1.message,
                'user': self.registry_1.user
            },
            'The the registry was updated with an empty message'
        )

    # ******* DESTROY
    def test_api_can_delete_a_registry(self):
        """ Test that the api can delete a registry """
        # Arrange:
        # Act:
        url = reverse(
            'shelveregistry-detail',
            kwargs={'pk': self.registry_1.pk}
        )
        self.response = self.client.delete(url, format='json')
        # Assert:
        retrieved_reg = list(
            ShelveRegistry.objects.filter(pk=self.registry_1.pk)
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_204_NO_CONTENT,
            'The server did not delete the registry'
        )
        self.assertEqual(retrieved_reg, [], 'The registry was not deleted')

    # ******* FILTER
    def test_api_can_filter_registries_by_alarm_and_status(self):
        """Test that the api can list the ShelveRegistrys filtered by alarm id
        and status"""
        # Arrange:
        new_registry_2 = ShelveRegistry.objects.create(
            alarm_id=self.registry_2.alarm_id,
            message='New message'
        )
        url = reverse('shelveregistry-filters')
        # Act:
        data = {
            'alarm_id': self.registry_2.alarm_id,
            'status': ShelveRegistryStatus.get_choices_by_name()['SHELVED']
        }
        self.response = self.client.get(url, data, format="json")
        expected_registries_data = [
            ShelveRegistrySerializer(new_registry_2).data
        ]
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the filtered registries'
        )
        retrieved_registries_data = self.response.data
        self.assertEqual(
            retrieved_registries_data,
            expected_registries_data,
            'The retrieved filtered registries do not match the expected ones'
        )
        # Act:
        data = {
            'alarm_id': self.registry_2.alarm_id,
            'status': ShelveRegistryStatus.get_choices_by_name()['UNSHELVED']
        }
        self.response = self.client.get(url, data, format="json")
        expected_registries_data = [
            ShelveRegistrySerializer(self.registry_2).data
        ]
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the filtered registries'
        )
        retrieved_registries_data = self.response.data
        self.assertEqual(
            retrieved_registries_data,
            expected_registries_data,
            'The retrieved filtered registries do not match the expected ones'
        )

    def test_api_can_filter_all_open_registries(self):
        """Test that the api can filter ShelveRegistrys by status """
        # Arrange:
        url = reverse('shelveregistry-filters')
        # Act:
        data = {
            'status': ShelveRegistryStatus.get_choices_by_name()['SHELVED']
        }
        self.response = self.client.get(url, data, format="json")
        expected_registries_data = [
            ShelveRegistrySerializer(self.registry_1).data,
            ShelveRegistrySerializer(self.registry_3).data,
        ]
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the filtered registries'
        )
        retrieved_registries_data = self.response.data
        self.assertEqual(
            retrieved_registries_data,
            expected_registries_data,
            'The retrieved filtered registries do not match the expected ones'
        )
        # Act:
        data = {
            'status': ShelveRegistryStatus.get_choices_by_name()['UNSHELVED']
        }
        self.response = self.client.get(url, data, format="json")
        expected_registries_data = [
            ShelveRegistrySerializer(self.registry_2).data,
        ]
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The Server did not retrieve the filtered registries'
        )
        retrieved_registries_data = self.response.data
        self.assertEqual(
            retrieved_registries_data,
            expected_registries_data,
            'The retrieved filtered registries do not match the expected ones'
        )

    # ******* UNSHELVE
    @mock.patch('tickets.connectors.AlarmConnector.unshelve_alarms')
    def test_api_can_unshelve_multiple_registries(
        self,
        AlarmConnector_unshelve_alarms
    ):
        """Test that the api can unshelve multiple ununshelved registries"""
        # Act:
        url = reverse('shelveregistry-unshelve')
        alarms_to_unshelve = ['alarm_1', 'alarm_2', 'alarm_3']
        expected_unshelved_alarms = ['alarm_1', 'alarm_3']
        data = {
            'alarms_ids': alarms_to_unshelve
        }
        self.response = self.client.put(url, data, format="json")
        # Assert:
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The status of the response is incorrect'
        )
        self.assertEqual(
            self.response.data,
            expected_unshelved_alarms,
            'The response is not as expected'
        )
        unshelved_registries = [
            ShelveRegistry.objects.get(pk=self.registry_1.pk),
            ShelveRegistry.objects.get(pk=self.registry_3.pk)
        ]
        expected_status = int(
            ShelveRegistryStatus.get_choices_by_name()['UNSHELVED']
        )
        self.assertTrue(
            unshelved_registries[0].status == expected_status and
            unshelved_registries[1].status == expected_status,
            'The registries were not correctly unshelved'
        )
        self.assertNotEqual(
            unshelved_registries[0].unshelved_at, None,
            'The first registry unshelving time was not correctly recorded'
        )
        self.assertNotEqual(
            unshelved_registries[1].unshelved_at, None,
            'The second registry unshelving time was not correctly recorded'
        )
        self.assertTrue(
            AlarmConnector_unshelve_alarms.called,
            'The alarm connector unshelve method should have been called'
        )

    @mock.patch('tickets.connectors.AlarmConnector.unshelve_alarms')
    def test_api_can_check_timeouts(
        self,
        AlarmConnector_unshelve_alarms
    ):
        """ Test that the api can check if active registries have timedout and
        notify accordingly """
        # Arrange:
        shelving_time = timezone.now()
        checking_time = shelving_time + datetime.timedelta(hours=2)
        with freeze_time(shelving_time):
            self.registries = [
                self.registry_1,
                self.registry_2,
                self.registry_3,
                ShelveRegistry.objects.create(
                    alarm_id='alarm_4',
                    message=self.message,
                    timeout=datetime.timedelta(hours=4)
                ),
                ShelveRegistry.objects.create(
                    alarm_id='alarm_5',
                    message=self.message,
                    timeout=datetime.timedelta(hours=1)
                ),
            ]
        expected_timedout = ['alarm_1', 'alarm_3', 'alarm_5']
        expected_status = \
            ShelveRegistryStatus.get_choices_by_name()['UNSHELVED']

        # Act:
        with freeze_time(checking_time):
            url = reverse('shelveregistry-check-timeouts')
            self.response = self.client.put(url, format="json")
        # Assert:
        unshelved_registries = list(
            ShelveRegistry.objects.filter(status=expected_status)
        )
        self.assertEqual(
            self.response.status_code,
            status.HTTP_200_OK,
            'The status of the response is incorrect'
        )
        self.assertEqual(
            self.response.data,
            expected_timedout,
            'The response is not as expected'
        )
        for reg in unshelved_registries:
            self.assertTrue(
                reg.status == expected_status,
                'The registries were not correctly unshelved'
            )
            self.assertNotEqual(
                reg.unshelved_at, None,
                'The regitries unshelving time was not correctly recorded'
            )
        self.assertTrue(
            AlarmConnector_unshelve_alarms.called,
            'The alarm connector unshelve method should have been called'
        )
        AlarmConnector_unshelve_alarms.assert_called_with(expected_timedout)
