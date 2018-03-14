FROM python:3.6.0

WORKDIR /usr/src/ias-webserver
COPY requirements.txt .
RUN pip install -r requirements.txt

RUN apt-get update && apt-get install netcat -y

COPY . .
RUN python manage.py makemigrations
RUN python manage.py migrate
RUN python manage.py migrate --database=cdb
RUN python manage.py collectstatic --noinput

VOLUME /usr/src/ias-webserver/static
EXPOSE 8001
ENTRYPOINT ["./entrypoint.sh"]
