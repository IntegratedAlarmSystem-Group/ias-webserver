# Generated by Django 2.0.8 on 2018-11-28 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('panels', '0009_auto_20181112_1850'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alarmconfig',
            name='custom_name',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='type',
            name='name',
            field=models.CharField(max_length=30, unique=True),
        ),
        migrations.AlterField(
            model_name='view',
            name='name',
            field=models.CharField(max_length=30, unique=True),
        ),
    ]