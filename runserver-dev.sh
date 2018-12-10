#!/bin/sh

# while ! nc -z postgres 5432
# do
#  echo "sleeping 1 second waiting for postgres"
#  sleep 1
# done

./load_fixtures.sh
python manage.py createusers --adminpassword ${ADMIN_PASSWORD} --operatorpassword ${OP_DUTY_PASSWORD}
python manage.py runserver 0.0.0.0:8000 &
python manage.py runtimers --hostname 0.0.0.0 --port 8000
