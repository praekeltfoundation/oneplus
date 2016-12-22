manage="${VENV}/bin/python ${INSTALLDIR}/${REPO}/manage.py"

$manage syncdb --noinput --no-initial-data --migrate
$manage collectstatic --noinput
$manage update_index --noinput

supervisorctl restart all
