#!/bin/bash
psql -c 'create database mobileu;' -U postgres
echo "DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql_psycopg2', 'NAME': 'mobileu', 'USER': 'postgres', 'PASSWORD': '', 'HOST': 'localhost', 'PORT': ''}}" > mobileu/production_settings.py
