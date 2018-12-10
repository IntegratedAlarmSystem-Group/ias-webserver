#!/bin/sh

if [ ${DB_ENGINE} == "mysql" ] || [ ${DB_ENGINE} == "oracle" ]
then
  while ! nc -z ${DB_HOST} ${DB_PORT}
  do
    echo "sleeping 1 second waiting for database"
    echo ${DB_HOST} ${DB_PORT}
    sleep 1
  done
fi

./load_fixtures.sh
python manage.py createusers --adminpassword ${ADMIN_PASSWORD} --operatorpassword ${OP_DUTY_PASSWORD}
daphne -b 0.0.0.0 -p 8000 ias_webserver.asgi:application & python manage.py runtimers --hostname 0.0.0.0 --port 8000
