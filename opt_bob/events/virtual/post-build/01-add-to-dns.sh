#!/bin/bash

FQDN="$2"
IP="$3"
HOST=$( echo $FQDN | awk -F. '{ print $1 }' )

echo "$IP  $FQDN  $HOST" >> /etc/hosts
