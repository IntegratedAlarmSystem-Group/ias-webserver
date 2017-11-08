# ias-webserver
IAS Web Server in Django Channels

## Installation Guide for development (on Ubuntu OS):

  1. Install system requirements `sudo apt-get install libpq-dev python3.6-dev python-pip python3-pip virtualenv redis-server`

  2. Create a virtualenvironment with python3: `virtualenv -p python3.6 venv`

  3. Activate virtualenv: `source venv/bin/activate`

  4. Install project requirements: `pip install -r requirements.txt`

## Local Execution
  * Activate virtual environment (if not already activated): `source venv/bin/activate`
  * Run development server: `python manage.py runserver`

## Run Tests
  * Run tests: `python manage.py test`
