from setuptools import setup, find_packages

setup(
    name='django-oneplus',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'django-mobileu',
        'psycopg2',
        'django_bleach',
        'beautifulsoup4',
    ],
    url='www.praekelt.co.za',
    license='',
    author='praekelt',
    author_email='info@praekelt.co.za',
    description='dig-it is a gamified mobile maths challenge portal for '
                'High School learners. It is built on the MobileU MOOC '
                'platform'
)
