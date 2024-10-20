#!/bin/bash

DB='opt_bob/robert/b-o-b.db'
SQL="sqlite3 $DB"

# for tbl in buildtemplate hero opsystem recipe
# do
#     $SQL "DROP TABLE $tbl"
# done

Tables=$( $SQL ".tables" )
echo $Tables

for tbl in $Tables
do
    echo "---------- $tbl ----------"
    $SQL ".schema $tbl"
    $SQL "SELECT * FROM $tbl"
done
