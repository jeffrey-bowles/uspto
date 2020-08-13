#!/bin/bash

kill $(ps aux | grep './manage.py runserver' | awk '{print $2}')
nohup ./manage.py runserver 0.0.0.0:12397 > devserver-"$(date +%Y%m%d_%H%M%S)".out &

exit 0
