#!/bin/env python3

from flask import Flask, redirect
import os
import threading
import time

app = Flask('wendy')


def follow_log(filename):
    print(f"Following {filename}")
    thefile = open(filename, 'rt')
    thefile.seek(0, os.SEEK_END)
    watermark = thefile.tell()
    while True:
        time.sleep(0.5)
        # try and seek
        thefile.seek(0, os.SEEK_END)
        new_end = thefile.tell()
        if watermark != new_end:
            thefile.seek(watermark)
            while watermark < new_end:
                line = thefile.readline()
                print(line, end='')
                watermark = thefile.tell()


@app.route("/")
def hello_world():
    return "Hello World !\n"


@app.route("/ping")
def ping_pong():
    return "pong\n"


@app.route("/file/<path:file_path>")
def get_file(file_path):
    return redirect(f"http://localhost/{file_path}", code=308)


@app.route("/api/complete/<mac>")
def complete_host(mac):
    os.system(f'/usr/local/sbin/bob complete {mac}')
    return "OK"


if __name__ == '__main__':
    x = threading.Thread(target=follow_log, args=('/var/log/messages',))
    x.start()
    # export FLASK_DEBUG=1
    app.run(port='5000', debug=True )
    # app.run(host='0.0.0.0')
