manage="${VENV}/bin/python ${INSTALLDIR}/${REPO}/manage.py"

$manage syncdb --noinput --no-initial-data --migrate
$manage collectstatic --noinput
${PIP} freeze > oneplusmvp/static/pip-freeze.txt
git log -50 --pretty=format:'%ai - %h %s (%cr) <%an>' > oneplusmvp/static/git-commits.log
