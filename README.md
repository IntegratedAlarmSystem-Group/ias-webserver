# ias-webserver
IAS Web Server in Django Channels

## Documentation
Documentation is available here:
https://integratedalarmsystem-group.github.io/ias-webserver/

## Installation Guide for development (on Ubuntu OS):

  1. Install system requirements `sudo apt-get install libpq-dev python3.6-dev python-pip python3-pip virtualenv redis-server`

  2. Create a virtualenvironment with python3: `virtualenv -p python3.6 venv`

  3. Activate virtualenv: `source venv/bin/activate`

  4. Install project requirements: `pip install -r requirements.txt`

## Installation Guide for development (on CentOS 7):

  1. Check the epel repository
  ```
  [ias-webserver]$ sudo yum install epel-release
  [ias-webserver]$ sudo yum -y update
  ```

  2. Install redis
  ```
  [ias-webserver]$ sudo yum install redis
  [ias-webserver]$ sudo systemctl start redis
  ```

  3. Install python36 and python36u-devel
  ```
  [ias-webserver]$ sudo yum -y install https://centos7.iuscommunity.org/ius-release.rpm
  [ias-webserver]$ sudo yum install python36u python36u-devel
  ```

  4. Install pip
  ```
  [ias-webserver]$ yum install -y install python-pip
  [ias-webserver]$ sudo pip install python36u
  ```

  5. Create and activate the virtual environment
  ```
  [ias-webserver]$ sudo pip install -U virtualenv
  [ias-webserver]$ virtualenv -p python36u venv
  [ias-webserver]$ source venv/bin/activate
  ```

  6. Install project requirements
  ```
  (venv)[ias-webserver]$ pip install -r requirements.txt
  ```

## Local Execution
  * Activate virtual environment (if not already activated): `source venv/bin/activate`
  * Run development server: `python manage.py runserver`
  * If required, apply migrations:
    - `python manage.py migrate`
    - `python manage.py migrate --database=cdb`

## Run Tests
  * Run tests: `pytest`
  * Run tests with coverage: `coverage run --source='.' manage.py test`
  * View coverage report in terminal:
    * Excluding third-party libraries in venv (recommended): `coverage report --omit='venv/*'`
    * Including third-party libraries: `coverage report`

## Update Documentation
  `./create_docs.sh`
