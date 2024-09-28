#!/bin/bash

cd /opt/bob/wendy

./follow-ngw-log.py &

gunicorn --bind 127.0.0.1:5000 wsgi:app
