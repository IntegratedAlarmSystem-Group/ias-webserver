#!/bin/sh

echo "Starting to load fixtures"
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata panels/fixtures/panels.files.json
python manage.py loaddata panels/fixtures/panels.alarm_config.json
python manage.py loaddata panels/fixtures/panels.pad_placemarks.json
echo "Finished loading fixtures"
