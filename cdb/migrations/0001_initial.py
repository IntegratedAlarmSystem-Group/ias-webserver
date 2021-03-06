# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-27 18:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Iasio',
            fields=[
                ('io_id', models.CharField(db_column='io_id', max_length=64, primary_key=True, serialize=False)),
                ('short_desc', models.TextField(db_column='shortDesc', max_length=256)),
                ('refresh_rate', models.IntegerField(db_column='refreshRate')),
                ('ias_type', models.CharField(db_column='iasType', max_length=16)),
            ],
            options={
                'db_table': 'IASIO',
            },
        ),
    ]
