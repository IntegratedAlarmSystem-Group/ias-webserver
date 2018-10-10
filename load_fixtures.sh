#!/bin/sh

echo "Starting to load fixtures"
python manage.py makemigrations
python manage.py migrate
python manage.py migrate --database=cdb
python manage.py loaddata cdb/fixtures/cdb.ias.json --database=cdb
python manage.py loaddata cdb/fixtures/cdb.iasios.json --database=cdb
python manage.py loaddata panels/fixtures/panels.files.json
python manage.py loaddata panels/fixtures/panels.alarm_config.json
python manage.py loaddata panels/fixtures/panels.pad_placemarks.json
echo "Fiished loading fixtures"
