MobileU MOOC
============

The MobileU MVP framework allows other developers to easily build mobile
education sites.

|mobileu-ci|_


Installation
~~~~~~~~~~~~

::

    $ virtualenv ve
    $ source ve/bin/activate
    (ve)$ pip install -r requirements.txt


Initial data
~~~~~~~~~~~~

To create permissions and groups run:

::

    $ source ve/bin/activate
    (ve)$ python manage.py syncdb --all
    (ve)$ python manage.py loaddata auth/fixtures/default_groups.json


Run Tests
~~~~~~~~~

::

    $ source ve/bin/activate
    (ve)$ python manage.py test



.. |mobileu-ci| image:: https://travis-ci.org/praekelt/mobileu.svg?branch=develop
.. _mobileu-ci: https://travis-ci.org/praekelt/mobileu
