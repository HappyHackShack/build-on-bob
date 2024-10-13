#!/bin/env python3

from flask import Flask

app = Flask('wendy')

from config import *
from api_pages import *
from cli_pages import *
from web_pages import *
