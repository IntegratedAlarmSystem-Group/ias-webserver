FROM python:3.6.0

WORKDIR /usr/src/ias-webserver
COPY requirements.txt .
RUN pip install -r requirements.txt

RUN apt-get update && apt-get install netcat -y

COPY . .
RUN python manage.py makemigrations
RUN python manage.py migrate
RUN python manage.py migrate --database=cdb
RUN python manage.py loaddata cdb/fixtures/cdb.ias.json --database=cdb
RUN python manage.py loaddata cdb/fixtures/cdb.iasios.json --database=cdb
RUN python manage.py collectstatic --noinput
RUN echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@fake-admin.com', 'nimda') if (User.objects.filter(username='admin').exists() == False) else None" | python manage.py shell
RUN find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

VOLUME /usr/src/ias-webserver/static
EXPOSE 8001
