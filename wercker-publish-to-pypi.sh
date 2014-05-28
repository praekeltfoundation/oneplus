echo "[server-login]" > ~/.pypirc
echo "username:" $PRAEKELT_PYPI_USER >> ~/.pypirc
echo "password:" $PRAEKELT_PYPI_PASSWORD >> ~/.pypirc
python setup.py sdist upload
