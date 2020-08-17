# Demo project using Python 3.6.9 / Django 3.0.8 / Vue.js 2.6.11 / Quasar 1.12.13

### Backend Installation Instructions

    sudo pip install virtualenv
    mkdir -p uspto
    cd uspto
    virtualenv .env --python=python3.6
    source .env/bin/activate
    pip install django==3.0.8
    pip install djangorestframework django-cors-headers
    pip install crontab
    django-admin startproject fees
    cd fees
    ./manage.py startapp pto
    ./manage.py makemigrations && ./manage.py migrate

to run server:

    ./reload-dev.sh

### Frontend Installation Instructions

    npm install -g @quasar/cli
    npm install axios
    quasar create qfront
    cd qfront

to run dev server:
    
    quasar dev


### Database/Cron Job Setup Instructions

after copying GitHub files run the following:

    ./initial-setup.sh

might take 1-2 days to populate all the data without the pre-existing SQL dump

Run the following command to add all the defined CRONJOBS in settings.py to crontab(*nix cron utility). Make sure to run this command every time CRONJOBS is changed in any way.
 
    ./manage.py crontab add

