#!/bin/bash

OVL='builder.apkovl.tar.gz'

[ -f $OVL ] && { echo "Exists :)"; exit 0; }

echo Building Generic Overlay ...

cd overlay
find . -type f -exec chmod 755 '{}' \;
find . -type d -exec chmod 755 '{}' \;

find . -type f -exec chown root: '{}' \;
find . -type d -exec chown root: '{}' \;

tar cv * | gzip -c9n > ../${OVL}

find . -type f -exec chown ${SUDO_USER}: '{}' \;
find . -type d -exec chown ${SUDO_USER}: '{}' \;
