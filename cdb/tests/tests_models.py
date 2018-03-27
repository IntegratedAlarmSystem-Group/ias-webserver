from django.test import TestCase
from cdb.models import Iasio, Ias, Property


class CdbModelsTestCase(TestCase):

    def tearDown(self):
        """TestCase teardown"""
        Iasio.objects.all().delete()
        Ias.objects.all().delete()
        Property.objects.all().delete()

    def test_create_iasio(self):
        """ Test if we can create an Iasio, with type in upper case"""
        # Act:
        iasio = Iasio(io_id='Test-ID',
                      short_desc='Test iasio',
                      ias_type='double')
        iasio.save()
        # Asserts:
        self.assertEqual(
            Iasio.objects.get(pk='Test-ID').ias_type, 'DOUBLE',
            'Ias type must be saved in upper case'
        )
        self.assertEqual(
            Iasio.objects.get(pk='Test-ID').get_data(),
            {
                'io_id': 'Test-ID',
                'short_desc': 'Test iasio',
                'ias_type': 'DOUBLE'
            },
            'The iasio obtained with get_data method is not the expected'
        )

    def test_create_ias(self):
        """ Test if we can create an Ias, with log_level in upper case
        and the refresh_rate and tolerance in miliseconds """
        # Act:
        ias = Ias(id=1, log_level='debug', refresh_rate=3, tolerance=1)
        ias.save()
        # Asserts:
        self.assertEqual(
            Ias.objects.get(pk=1).get_data(),
            {
                'log_level': 'DEBUG',
                'refresh_rate': 3,
                'tolerance': 1,
                'properties': []
            },
            'The ias obtained with get_data method is not the expected'
        )

    def test_create_property(self):
        """ Test if we can create a Property, an add the relation with an Ias
        object """
        # Act:
        prop = Property(id=1, name='prop1', value='value1')
        prop.save()
        # Assert:
        self.assertEqual(
            Property.objects.get(pk=1).get_data(),
            {
                'name': 'prop1',
                'value': 'value1'
            },
            'The property obtained with get_data method is not the expected'
        )

    def test_add_ias_property_relation(self):
        """ Test if we can add a relation between an ias and a property """
        # Arrange:
        prop = Property(id=1, name='prop1', value='value1')
        prop.save()
        ias = Ias(id=1, log_level='debug', refresh_rate=3, tolerance=1)
        ias.save()
        # Act:
        ias.properties.add(prop)
        # Assert:
        self.assertEqual(
            Ias.objects.get(pk=1).get_data(),
            {
                'log_level': 'DEBUG',
                'refresh_rate': 3,
                'tolerance': 1,
                'properties': [{'name': 'prop1', 'value': 'value1'}]
            },
            'The ias with property obtained with get_data method is not \
            the expected'
        )
