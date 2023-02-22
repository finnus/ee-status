# EE-Status

Displaying Data from the "Marktstammdatenregister". You can currently explore it at https://ee-status.herokuapp.com/ .
This project is currently a (technical) "Proof of concept". It lacks tests, proper documentation and a good structure.
[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

License: GPLv3

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Get the data
 * thank open-MaStR for their great efforts which make this project here possible in the first place
 * get the data with help from open-MaStR
   * get open-MaStR: https://github.com/OpenEnergyPlatform/open-MaStR via pip (use conda or virtualenv): pip install open-mastr
   * RTD: https://open-mastr.readthedocs.io/en/latest/getting_started.html#
   * or just do in python console:
     * from open_mastr import Mastr
     * db = Mastr()
     * db.download(data=["solar","wind","biomass","hydro","storage"]) # we don't need all data

### Import data wit pgloader
 * import the population and area data (from another source, saved inside sql_scripts/municipality_key_import_file.csv)
   * run pgloader: pgloader sql_scripts/01_import_municipality_keys
 * run pgloader transform data from open-MaStR: pgloader sql_scripts/02_import_from_open-mastr
   * adapt path to open_MaStR to your needs; data usually gets downloaded to /home/$USER
   * pgloader will also run the script 03_unite_tables.sql

### Import the newly created tables into your django postgres database
 * import the tables 'current_totals', 'energy_units' and 'monthly_timeline' into your Django project
 * run Django as usual "python manage.py runserver"

### Setting Up Your Users
-   To create a **superuser account**, use this command:

        $ python manage.py createsuperuser
-
### Type checks

Running type checks with mypy:

    $ mypy ee_status

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with pytest

    $ pytest

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=cookiecutter> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

## Deployment

The following details how to deploy this application.

### Heroku

See detailed [cookiecutter-django Heroku documentation](http://cookiecutter-django.readthedocs.io/en/latest/deployment-on-heroku.html).
