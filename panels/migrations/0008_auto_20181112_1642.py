# Generated by Django 2.0.8 on 2018-11-12 16:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('panels', '0007_auto_20181112_1414'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='placemark',
            options={'default_permissions': ('add', 'change', 'delete', 'view')},
        ),
    ]