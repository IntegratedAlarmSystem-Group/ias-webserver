FROM centos:7

# Install python
RUN yum install -y https://centos7.iuscommunity.org/ius-release.rpm &&\
  yum -y update
RUN yum install -y gcc python36u python36u-devel python36u-pip
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.6 1 &&\
  update-alternatives --install /usr/bin/pip pip /usr/bin/pip3.6 1

# Install requirements
WORKDIR /usr/src/ias-webserver
COPY requirements.txt .
RUN pip install -r requirements.txt


# Copy source files and build project
COPY . .
RUN python manage.py makemigrations
RUN python manage.py migrate
RUN python manage.py migrate --database=cdb
RUN python manage.py loaddata cdb/fixtures/cdb.ias.json --database=cdb
RUN python manage.py loaddata cdb/fixtures/cdb.iasios.json --database=cdb
RUN python manage.py collectstatic --noinput
RUN echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@fake-admin.com', 'nimda') if (User.objects.filter(username='admin').exists() == False) else None" | python manage.py shell
RUN find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

# Expose static files and port
VOLUME /usr/src/ias-webserver/static
EXPOSE 8001
