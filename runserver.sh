#!/bin/sh

# while ! nc -z postgres 5432
# do
#  echo "sleeping 1 second waiting for postgres"
#  sleep 1
# done

# echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@fake-admin.com', 'nimda') if (User.objects.filter(username='admin').exists() == False) else None" | python manage.py shell

daphne -b 0.0.0.0 -p 8001 ias_webserver.asgi:application & python manage.py runtimers --hostname 0.0.0.0 --port 8001
