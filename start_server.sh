#!/bin/bash
source /home/ludo/Documents/Dev/Cyonima-ES-Tooling/venv/bin/activate
cd /home/ludo/Documents/Dev/Cyonima-ES-Tooling
exec python manage.py runserver 127.0.0.1:8080 --noreload
