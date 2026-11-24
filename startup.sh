#!/bin/bash
# Azure App Service startup command.
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn --bind=0.0.0.0 --timeout 120 --workers "${GUNICORN_WORKERS:-3}" InventoryMS.wsgi
