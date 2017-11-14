# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-10 21:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alarms', '0002_alarm_mode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alarm',
            name='mode',
            field=models.CharField(choices=[('2', 'closing'), ('6', 'degraded'), ('1', 'initialization'), ('4', 'maintenance'), ('5', 'operational'), ('3', 'shuttedown'), ('0', 'startup'), ('7', 'unknown')], default=0, max_length=1),
        ),
    ]