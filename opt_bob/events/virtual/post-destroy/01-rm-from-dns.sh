#!/bin/bash

FQDN="$2"
TMPF="/tmp/hosts.$( uuidgen )"

cp /etc/hosts "$TMPF"
grep -v "$FQDN" "$TMPF" > /etc/hosts

rm -f "$TMPF"
