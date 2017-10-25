# ias-webserver
IAS Web Server in Django Channels

## Installation Guide on Ubuntu OS:

  1. Install system requirements `sudo apt-get install libpq-dev python3.6-dev python-pip python3-pip virtualenv`

  2. Create a virtualenvironment with python3: `virtualenv -p python3.6 venv`

  3. Activate virtualenv: `source venv/bin/activate`

  4. Install project requirements: `pip install -r requirements.txt`

## Local Execution
  * Activate virtual environment (if not already activated): `source venv/bin/activate`
  * Run development server: `python manage.py runserver`

## Run Tests
  * Run tests: `python manage.py test`
  * Run tests with coverage: `coverage run --source='.' manage.py test`
  * View coverage report in terminal:
    * Excluding third-party libraries in venv (recommended): `coverage report --omit='venv/*'`
    * Including third-party libraries: `coverage report`
  * View coverage report in website:
    * Excluding third-party libraries in venv (recommended): `coverage html --omit='venv/*'`
    * Including third-party libraries: `coverage html`
    * Open report: `<browser-command> htmlcov/index.html`, e.g:
      * Google Chrome: `google-chrome htmlcov/index.html`
      * Firefox: `firefox htmlcov/index.html`
