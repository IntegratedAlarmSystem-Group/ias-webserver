# Generated by Django 2.0.4 on 2018-07-31 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=30, unique=True)),
                ('url', models.CharField(max_length=256)),
            ],
        ),
    ]
