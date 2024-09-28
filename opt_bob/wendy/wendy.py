#!/bin/env python3

from flask import Flask
import os

app = Flask('wendy')


@app.route("/")
def hello_world():
    return "Hello World !"


@app.route("/ping")
def ping_pong():
    return "pong"


@app.route("/complete/<mac>")
def complete_host(mac):
    os.system(f'/usr/local/sbin/bob complete {mac}')
    return "OK"


if __name__ == '__main__':
    # export FLASK_DEBUG=1
    app.run(port='5000', debug=True )
    # app.run(host='0.0.0.0')
