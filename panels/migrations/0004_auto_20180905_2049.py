# Generated by Django 2.0.4 on 2018-09-05 20:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('panels', '0003_auto_20180831_1506'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alarmconfig',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='nested_alarms', to='panels.AlarmConfig'),
        ),
    ]
