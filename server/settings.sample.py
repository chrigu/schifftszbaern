# -*- coding: utf-8 -*-

# Server stuff
#############
DEBUG = True

SERVER = 'http://127.0.0.1:5000'

SERVER_DATA_FILE = '.server_data.json'

RAIN_UPDATE_PATH = '/someurl_rain'
WEATHER_UPDATE_PATH = '/someurl_weather'

SECRET = 'secret'
DUNNO_MESSAGE = u'Weiss nümme'
DISPLAY_DATE_FORMAT = '%d.%m.%Y %H:%M'

USE_MONGODB = False
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017

SERVER_RAIN_MESSAGE = "S'schifft"
SERVER_DRY_MESSAGE = "S'isch troche"
SERVER_SNOW_MESSAGE = "S'schneit"
SERVER_RAIN_SINCE_MESSAGE = "S'schifft sit"
SERVER_DRY_SINCE_MESSAGE = "S'isch troche sit"
SERVER_SNOW_SINCE_MESSAGE = "S'schneit sit"