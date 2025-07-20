#!/usr/bin/env sh

echo "Migrations"
alembic upgrade head || exit
echo "Run server"

gunicorn -c docker/gunicorn_config.py main:app