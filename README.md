# uspto
Demo project using Python 3.6.9 / Django 3.0.8 / Vue.js 2.6.11 / Quasar 1.12.13

Installation Instructions

sudo pip install virtualenv

mkdir -p uspto
cd uspto
virtualenv .env --python=python3.6
source .env/bin/activate
pip install django==3.0.8
pip install crontab
pip install djangorestframework django-cors-headers
django-admin startproject fees
cd fees
./manage.py startapp pto
python manage.py makemigrations && python manage.py migrate
to run server:

./reload-dev.sh


# nodeenv

npm install -g @quasar/cli
npm install axios
quasar create qfront
cd qfront

to run dev server:
quasar dev



after copying GitHub files:

change database settings
run the following:

./initial-setup.sh

might take 1-2 days to populate all the data without the pre-existing SQL dump

Add cron jobs
./manage.py crontab add

