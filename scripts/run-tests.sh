#!/bin/sh
python manage.py syncdb | tee
python manage.py migrate
python manage.py syncdb --all --noinput  # call AFTER migrations for permission creation
coverage run --source=oneplus manage.py test --verbosity=2 --noinput