from setuptools import setup, find_packages

setup(
    name='django-mobileu',
    version='1.1.0',
    packages=find_packages(),
    install_requires=[
        'Django==1.6.5',
        'South==0.8.4',
        'Celery',
        'django-grappelli==2.5.3',
        'django-summernote==0.5.13',
        'django-import-export==0.2.2',
        'django-celery',
        'Pillow==2.4.0',
        'psycopg2==2.5.3',
        'koremutake==1.0.5',
        'requests==2.3.0',
        'go_http==0.1.1',
        'django_bleach',
        'beautifulsoup4',
    ],
    url='www.praekelt.co.za',
    license='',
    author='praekelt',
    author_email='info@praekelt.co.za',
    description='The MobileU MVP framework allows other developers to '
                'easily build mobile education sites.'
)
