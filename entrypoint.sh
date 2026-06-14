#!/bin/sh
set -e

echo "-> Running migrations..."
python manage.py migrate --noinput
echo "-> Migrations complete."

# If arguments are provided, run them (e.g. CMD override), otherwise start server
if [ "$#" -gt 0 ]; then
	exec "$@"
else
	exec python manage.py runserver 0.0.0.0:8000
fi