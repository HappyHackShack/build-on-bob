#!/bin/bash

mkdir -p static/{bs-5.3.3,fa-6.6.0,webfonts}

cd static/bs-5.3.3
wget -nc 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css'
cd ../fa-6.6.0
wget -nc 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css'
cd ../webfonts
wget -nc 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/webfonts/fa-solid-900.woff2'
#wget -nc 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/webfonts/fa-solid-900.ttf'
