# Generated by Django 2.0.4 on 2018-11-08 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0008_auto_20180730_2035'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='user',
            field=models.CharField(max_length=150, null=True),
        ),
    ]
