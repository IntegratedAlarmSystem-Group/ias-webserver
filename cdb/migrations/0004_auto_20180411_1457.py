# Generated by Django 2.0.2 on 2018-04-11 14:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdb', '0003_auto_20180322_2013'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ias',
            options={'verbose_name_plural': 'ias'},
        ),
        migrations.AlterModelOptions(
            name='property',
            options={'verbose_name_plural': 'properties'},
        ),
    ]
