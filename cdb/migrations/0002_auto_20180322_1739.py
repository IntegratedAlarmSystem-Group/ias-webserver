# Generated by Django 2.0.2 on 2018-03-22 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cdb', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ias',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('log_level', models.CharField(db_column='logLevel', max_length=10)),
                ('refresh_rate', models.IntegerField(db_column='refreshRate')),
                ('tolerance', models.IntegerField()),
            ],
            options={
                'db_table': 'IAS',
            },
        ),
        migrations.RemoveField(
            model_name='iasio',
            name='refresh_rate',
        ),
    ]
