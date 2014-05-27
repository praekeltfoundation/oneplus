#!/bin/bash
psql -c 'create database oneplusmvp;' -U postgres
echo "DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql_psycopg2', 'NAME': 'oneplusmvp', 'USER': 'postgres', 'PASSWORD': '', 'HOST': 'localhost', 'PORT': ''}}" > oneplusmvp/production_settings.py
