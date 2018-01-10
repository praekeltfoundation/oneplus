from setuptools import setup, find_packages

setup(
    name='django-mobileu',
    version='1.1.8',
    packages=find_packages(),
    install_requires=[
        'Celery==3.1.12',
        'Django==1.6.5',
        'Pillow==2.4.0',
        'South==0.8.4',
        'beautifulsoup4==4.5.0',
        'coverage',
        'django-celery==3.1.16',
        'django-grappelli==2.5.5',
        'django-import-export==0.4.5',
        'django-summernote==0.6.8',
        'django-bleach==0.3.0',
        'bleach==1.5.0',
        'elasticsearch>=5,<6',
        'go_http==0.1.1',
        'koremutake==1.0.5',
        'mock==1.0.1',
        'psycopg2==2.5.3',
        'pyDNS',
        'requests==2.3.0',
        'responses==0.5.1',
        'validate_email',
        'xlwt',
        'django-daterange-filter'
    ],
    url='www.praekelt.co.za',
    license='',
    author='praekelt',
    author_email='info@praekelt.co.za',
    description='The MobileU MVP framework allows other developers to '
                'easily build mobile education sites.'
)
