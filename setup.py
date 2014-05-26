from distutils.core import setup

setup(
    name='django-mobileu',
    version='1.04',
    packages=['auth', 'auth.migrations', 'core', 'core.migrations', 'content', 'content.migrations', 'mobileu',
              'gamification', 'gamification.migrations', 'organisation', 'organisation.migrations', 'communication',
              'communication.migrations'],
    install_requires=[
        'Django==1.6.5',
        'South==0.8.4',
    ],
    url='www.preakelt.co.za',
    license='',
    author='preakelt',
    author_email='info@preakelt.co.za',
    description='The MobileU MVP framework allows other developers to easily build mobile education sites.'
)
