#!/bin/bash

case "$1" in
    c|curtis)
        cd opt_bob/curtis
        flask --debug --app main run --port 8001
        ;;
    r|robert) 
        cd opt_bob/robert
        fastapi dev main.py --port 7999
        ;;
esac
