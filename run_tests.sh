coverage run --source="mobileu,core,auth,communication,content,gamification,organisation" --omit="*migrations*,*wsgi*" manage.py test
coverage html
firefox ./htmlcov/index.html
