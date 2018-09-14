# Generated by Django 2.0.4 on 2018-08-30 19:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('panels', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlarmConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alarm_id', models.CharField(max_length=64)),
                ('placemark', models.CharField(blank=True, max_length=15, null=True)),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='nested_alarms', to='panels.AlarmConfig')),
            ],
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='View',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=15)),
            ],
        ),
        migrations.AddField(
            model_name='alarmconfig',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alarms', to='panels.Type'),
        ),
        migrations.AddField(
            model_name='alarmconfig',
            name='view',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alarms', to='panels.View'),
        ),
        migrations.AlterUniqueTogether(
            name='alarmconfig',
            unique_together={('alarm_id', 'view')},
        ),
    ]
