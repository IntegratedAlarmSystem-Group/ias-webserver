# Generated by Django 2.0.2 on 2018-04-11 14:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0002_auto_20180411_1408'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ticket',
            old_name='resolve_at',
            new_name='resolved_at',
        ),
    ]