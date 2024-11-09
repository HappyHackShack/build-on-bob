#!/bin/env python3

import logging
import os
import time

NGINX_WENDY_LOG = "/var/log/nginx/wendy.log"
BUILD_STATUS = "/tmp/build_status"
TITLE = "BOB Build Status\n\n"

# Setup Logging
logging.basicConfig(
    filename="/tmp/follow.log",
    level=logging.INFO,
    encoding="utf-8",
    filemode="a",
    format="{asctime}|{message}",
    style="{",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)

with open(BUILD_STATUS, "wt") as bstat:
    bstat.write(TITLE)


def follow(filename):
    thefile = open(filename, "rt")
    thefile.seek(0, os.SEEK_END)
    cur_pos = thefile.tell()
    while True:
        time.sleep(0.5)
        # try and seek
        thefile.seek(0, os.SEEK_END)
        new_pos = thefile.tell()
        if cur_pos != new_pos:
            thefile.seek(cur_pos)
            while cur_pos < new_pos:
                line = thefile.readline()
                bits = line.split()
                ip = bits[1]
                url = bits[4]
                if "ipxe" in url:
                    stage = 1 if "stage1" in url else 2
                if "rescue" in url:
                    if "vmlinuz" in url:
                        stage = 3
                    if "initr" in url:
                        stage = 4
                    if "modloop" in url:
                        stage = 6
                if "build" in url:
                    if "apkovl" in url:
                        stage = 5
                    if ":" in url and url[-2:] == "sh":
                        stage = 7
                    if "meta" in url:
                        stage = 9
                    if "user" in url:
                        stage = 10
                if "raw.gz" in url:
                    stage = 8
                if "api/complete" in url:
                    stage = 11

                Stages = [
                    "iPXE1",
                    "iPXE2",
                    "KERN",
                    "INTRD",
                    "OVL",
                    "MOD",
                    "Bash",
                    "IMG",
                    "Meta",
                    "User",
                    "Done",
                ]
                progress = " ".join(Stages[:stage])
                remaining = " ".join(Stages[stage:])
                msg = f"{ip} is on stage {stage} | \x1b[32m{progress} \x1b[90m{remaining}\x1b[0m\n"
                cur_pos = thefile.tell()
                #
                with open(BUILD_STATUS, "wt") as bstat:
                    bstat.write(TITLE)
                    bstat.write(msg)


follow(NGINX_WENDY_LOG)
