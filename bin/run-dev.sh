#!/bin/bash

case "$1" in
    r|robert) 
        cd opt_bob/robert
        fastapi dev main.py --port 7999
        ;;
    w|wendy)
        cd opt_bob/wendy
        flask --debug --app wendy run --port 8080
        ;;
esac
