#!/bin/sh

# while ! nc -z ${DB_HOST} ${DB_PORT}
# do
#  echo "sleeping 1 second waiting for database"
#  sleep 1
# done

# echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@fake-admin.com', 'nimda') if (User.objects.filter(username='admin').exists() == False) else None" | python manage.py shell
./load_fixtures.sh
# python manage.py collectstatic --noinput
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@fake-admin.com', 'nimda') if (User.objects.filter(username='admin').exists() == False) else None" | python manage.py shell
daphne -b 0.0.0.0 -p 8000 ias_webserver.asgi:application & python manage.py runtimers --hostname 0.0.0.0 --port 8000
