# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-13 16:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alarms', '0004_auto_20171206_2149'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alarm',
            name='core_id',
            field=models.CharField(db_index=True, max_length=100),
        ),
    ]