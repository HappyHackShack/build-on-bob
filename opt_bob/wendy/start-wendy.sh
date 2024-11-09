#!/bin/bash

My_Dir=$( realpath $0)

# If we are under /home - assume debug mode
if [[ ${My_Dir::5} == '/home' ]]
then
    cd $( dirname $My_Dir )
    rsync -av --chown=root:root static /usr/share/nginx/html/
    flask --debug --app wendy run &
    fastapi dev wendy_api.py --port 8080 &
else
    cd /opt/bob/wendy
    ./follow-ngw-log.py &
    gunicorn --bind 127.0.0.1:5000 wendy:app &
    fastapi run wendy_api.py --host 127.0.0.1 --port 8080 &
fi
