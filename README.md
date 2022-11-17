# EE-Status

Displaying Data from the "Marktstammdatenregister".

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

License: GPLv3

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Basic Commands

### Setting Up Your Users

-   To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

-   To create a **superuser account**, use this command:

        $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

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

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/developing-locally.html#sass-compilation-live-reloading).

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=cookiecutter> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

## Deployment

The following details how to deploy this application.

### Heroku

See detailed [cookiecutter-django Heroku documentation](http://cookiecutter-django.readthedocs.io/en/latest/deployment-on-heroku.html).


### Get the data
 * thank open-MaStR for their great efforts which make this project here possible in the first place
 * get the data with help from open-MaStR
   * get open-MaStR: https://github.com/OpenEnergyPlatform/open-MaStR via pip (use conda or virtualenv): pip install open-mastr
   * RTD: https://open-mastr.readthedocs.io/en/latest/getting_started.html#
   * or just do in python console:
     * from open_mastr import Mastr
     * db = Mastr()
     * db.download()

### Import data wit pgloader
 * run pgloader transform data from open-MaStR: pgloader sql_scripts/01_import_from_open-mastr
   * adapt path to open_MaStR to your needs; data usually gets downloaded to /home/$USER
 * pgloader will also run the script 03_unite_tables.sql
 * run pgloader a second time to import "population" and "area" from csv:
 * pgloader will also run the script 04_timescaledb_hypertable.sql

### Transform the table into a TimescaleDB hypertable
 * run sql_scripts/04_timescaledb_hypertable.sql to create the hypertable and the view for monthly data
 * import the newly created materialized view 'monthly_energy_source' into django
 * run Django as usual "python manage.py runserver" and browse to /energy_sources/timeline
