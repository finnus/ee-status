# EE Status

Displaying data from the German Marktstammdatenregister. You can currently explore it at <https://ee-status.de/>.

[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

License: GPLv3

## Settings

Moved to [settings](https://cookiecutter-django.readthedocs.io/en/latest/1-getting-started/settings.html).

## Running it locally

Everything runs in Docker; there is no host-level Python setup.

    docker compose -f docker-compose.local.yml build
    docker compose -f docker-compose.local.yml up

The site is then on <http://localhost:8000>, Mailpit on <http://localhost:8025>, and
Postgres on host port **5433** (5432 inside the container).

Any `manage.py` command runs through the `django` service:

    docker compose -f docker-compose.local.yml run --rm django python manage.py createsuperuser

### Getting the data

The three data tables (`current_totals`, `monthly_timeline`, `energy_units`) are
**not** created by Django — they are `managed = False` models over tables built by
the import pipeline below. Without them the site has nothing to show.

The quickest way to get a working local database is to restore a dump of the
production database:

    docker compose -f docker-compose.local.yml up -d postgres
    docker compose -f docker-compose.local.yml cp <the-dump>.dmp postgres:/tmp/dump.dmp
    docker compose -f docker-compose.local.yml exec postgres \
      pg_restore -U $POSTGRES_USER -d $POSTGRES_DB --no-owner --no-privileges /tmp/dump.dmp

`$POSTGRES_USER` / `$POSTGRES_DB` are the values in `.envs/.local/.postgres`. The
three `CREATE SCHEMA` errors that `pg_restore` reports for `tiger`, `tiger_data`
and `topology` are expected — the PostGIS image already ships those schemas.

Dumps are gitignored (`*.dmp`); never commit one.

### Rebuilding the data from scratch

Thanks to [open-MaStR](https://github.com/OpenEnergyPlatform/open-MaStR) for the
effort that makes this project possible in the first place.

1. Download the raw data with open-MaStR (see its
   [getting started guide](https://open-mastr.readthedocs.io/en/latest/getting_started.html)):

       from open_mastr import Mastr
       db = Mastr()
       db.download(data=["solar", "wind", "biomass", "hydro", "storage"])

2. Import the population and area figures:
   `pgloader sql_scripts/01_import_municipality_keys`
3. Transform the open-MaStR data: `pgloader sql_scripts/02_import_from_open-mastr`
   (adapt the path to your open-MaStR download first). This also runs
   `sql_scripts/03_unite_tables.sql`, which builds the three tables above.

Note that these scripts are not yet wired into the Docker setup and still write to
a database called `solar`; the resulting tables have to be moved into the
application database by hand.

## Basic Commands

### Setting Up Your Users

- To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

- To create a **superuser account**, use this command:

      uv run python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    docker compose -f docker-compose.local.yml run --rm django mypy ee_status

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report:

    uv run coverage run -m pytest
    uv run coverage html
    uv run open htmlcov/index.html

#### Running tests with pytest

    uv run pytest

### Live reloading and Sass CSS compilation

Moved to [Live reloading and SASS compilation](https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally.html#using-webpack-or-gulp).

### Email Server

In development, it is often nice to be able to see emails that are being sent from your application. For that reason local SMTP server [Mailpit](https://github.com/axllent/mailpit) with a web interface is available as docker container.

Container mailpit will start automatically when you will run all docker containers.
Please check [cookiecutter-django Docker documentation](https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally-docker.html) for more details how to start all containers.

With Mailpit running, to view messages that are sent by your application, open your browser and go to `http://127.0.0.1:8025`

### Sentry

Sentry is an error logging aggregator service. You can sign up for a free account at <https://sentry.io/signup/?code=cookiecutter> or download and host it yourself.
The system is set up with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.

## Deployment

Deployment is handled by **Coolify**, which builds `docker-compose.production.yml`.

Coolify runs its own reverse proxy and terminates TLS, so — unlike the stock
cookiecutter-django setup — this repository ships neither Traefik nor nginx. The
`django` service exposes port **5000** (gunicorn) for Coolify's proxy to route to.
The production stack is therefore just three services: `django`, `postgres`
(PostGIS) and `redis`.

Configuration comes from `.envs/.production/.django` and `.envs/.production/.postgres`;
set those as environment variables in Coolify rather than committing them (both are
gitignored — only `.envs/.local/` is tracked).

The site is a public, read-only view onto the MaStR data and has no user accounts,
so `DJANGO_ACCOUNT_ALLOW_REGISTRATION` should be set to `False` in Coolify. Create
the admin account with `createsuperuser` instead.

For background on the compose setup, see the
[cookiecutter-django Docker documentation](https://cookiecutter-django.readthedocs.io/en/latest/3-deployment/deployment-with-docker.html).

### Database backups

The Postgres image carries cookiecutter's maintenance scripts:

    docker compose -f docker-compose.production.yml exec postgres backup
    docker compose -f docker-compose.production.yml exec postgres backups
    docker compose -f docker-compose.production.yml exec postgres restore <filename>
