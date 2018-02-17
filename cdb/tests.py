from django.test import TestCase
from .models import Iasio


class IasioModelTestCase(TestCase):

    def tearDown(self):
        """TestCase teardown"""
        Iasio.objects.all().delete()

    def test_create_iasio(self):
        # Act:
        iasio = Iasio(io_id='Test-ID',
                      short_desc='Test iasio',
                      refresh_rate=1000,
                      ias_type='double')
        iasio.save()
        # Asserts:
        self.assertEqual(
            Iasio.objects.get(pk='Test-ID').ias_type, 'DOUBLE',
            'Ias type must be saved in upper case'
        )
