#!/bin/bash

echo -n "BoB DB Initialization: "
curl -X POST http://localhost:7999/initialise/database
echo

echo Subnets:

./bob.py sn l | grep 172.16.0.0 > /dev/null || (
    echo Adding 172.16.0.0; 
    ./bob.py sn a 172.16.0.0/24 172.16.0.254 172.16.0.254;
)
./bob.py sn l


echo Hosts:

./bob.py h l | grep lucy > /dev/null || (
    echo Adding lucy; 
    ./bob.py h a lucy '172.16.0.12' 'e4:b9:7a:0b:bf:97';
)
./bob.py h l
