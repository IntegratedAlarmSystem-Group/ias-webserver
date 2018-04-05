# ias-webserver
IAS Web Server in Django Channels

## Documentation
Documentation is available here:
https://integratedalarmsystem-group.github.io/ias-webserver/

All the instructions below should be executed form the project root folder, unless otherwise stated

## Installation Guide for development (on Ubuntu OS):

  1. Install system requirements
  ```
  sudo apt-get install libpq-dev python3.6-dev python-pip python3-pip virtualenv redis-server
  ```
  2. Create a virtualenvironment with python3:
  ```
  virtualenv -p python3.6 venv
  ```
  3. Activate virtualenv:
  ```
  source venv/bin/activate
  ```
  4. Install project requirements:
  ```
  pip install -r requirements.txt
  ```

## Installation Guide for development (on CentOS 7):

  1. Check the epel repository
  ```
  sudo yum install epel-release
  sudo yum -y update
  ```
  2. Install redis
  ```
  sudo yum install redis
  sudo systemctl start redis
  ```
  3. Install python36 and python36u-devel
  ```
  sudo yum -y install https://centos7.iuscommunity.org/ius-release.rpm
  sudo yum install python36u python36u-devel
  ```
  4. Install pip
  ```
  yum install -y install python-pip
  sudo pip install python36u
  ```
  5. Create and activate the virtual environment
  ```
  sudo pip install -U virtualenv
  virtualenv -p python36u venv
  source venv/bin/activate
  ```
  6. Install project requirements
  ```
  pip install -r requirements.txt
  ```

## Run natively
### Run application:
  * Activate virtual environment (if not already activated):
  ```
  source venv/bin/activate
  ```
  * Run development server:
  ```
  python manage.py runserver
  ```
  * Run broadcast command:
  ```
  python manage.py broadcaststatus --hostname <HOST> --port <PORT> --rate <RATE IN SECS>
  ```
  * If required, apply migrations:
  ```
  python manage.py migrate && python manage.py migrate --database=cdb
  ```

### Run Tests:
  * Run tests:
  ```
  pytest
  ```
  * Run tests with coverage:
  ```
  coverage run --source='.' manage.py test
  ```
  * View coverage report in terminal:
    * Excluding third-party libraries in venv (recommended):
    ```
    coverage report --omit='venv/*'
    ```
    * Including third-party libraries:
    ```
    coverage report
    ```

## Run with Docker
### Run application:
  * Create docker image with name "webserver_image":
  ```
  docker build -t webserver_image .
  ```
  * Run with production server
  ```
  docker run webserver_image ./runserver.sh
  ```
  * Run with development server
  ```
  docker run webserver_image ./runserver-dev.sh
  ```

### Run Tests:
  * Create docker image with name "webserver_image" (if not already created):
  ```
  docker build -t webserver_image .
  ```
  * Run tests:
  ```
  docker run webserver_image ./runtests.sh
  ```


## Update Documentation
  ```
  ./create_docs.sh
  ```
