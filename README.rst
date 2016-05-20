dig-it
=======

|oneplus-ci|_ |oneplus-coverage|_

.. |oneplus-ci| image:: https://travis-ci.org/praekelt/oneplus.svg?branch=develop
.. _oneplus-ci: https://travis-ci.org/praekelt/oneplus

.. |oneplus-coverage| image:: https://coveralls.io/repos/praekelt/oneplus/badge.png?branch=develop 
.. _oneplus-coverage: https://coveralls.io/r/praekelt/oneplus


Installation
~~~~~~~~~~~~

::

    $ createdb -U oneplus oneplus
    $ virtualenv ve
    $ source ve/bin/activate
    (ve)$ pip install -r requirements.txt
    (ve)$ ./manage.py syncdb --migrate
    (ve)$ ./manage.py migrate

Run Tests
~~~~~~~~~

::

    $ source ve/bin/activate
    (ve)$ ./manage.py test
