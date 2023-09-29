#!/bin/sh

python manage.py collectstatic --noinput
python manage.py compilemessages
python manage.py migrate
gunicorn config.wsgi --bind=0.0.0.0:80
