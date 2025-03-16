#!/bin/bash
# entrypoint.sh

echo "Waiting for postgres..."
while ! nc -z postgres 5432; do
  sleep 0.5
done
echo "PostgreSQL started"

echo "Running database migrations..."
flask db upgrade

echo "Starting Gunicorn server..."
exec gunicorn -w 3 -b 0.0.0.0:5000 manage:app
