#!/bin/bash
set -e

echo "==> Cyonima-ES-Tools — Démarrage"

echo "==> Migrations"
python manage.py migrate --noinput

echo "==> Collecte statique"
python manage.py collectstatic --noinput 2>/dev/null || true

echo "==> Serveur prêt sur http://0.0.0.0:8080"
exec "$@"
