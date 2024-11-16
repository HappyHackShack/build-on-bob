#!/bin/bash

FQDN="$1"
IP="$2"
HOST=$( echo $FQDN | awk -F. '{ print $1 }' )

echo "$IP  $FQDN  $HOST" >> /etc/hosts
