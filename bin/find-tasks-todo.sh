#/!bin/bash

grep -r --exclude-dir=.venv 'TODO' *
