# -*- coding: utf-8 -*-

#GENERAL
########
DEBUG = True
DATE_FORMAT = "%Y%m%d%H%M00"

#The location's position
########################

#Berne, Baby, Berne!
X_LOCATION = 364
Y_LOCATION = 366

#location for radarimages
RADAR_IMAGES = '/Path/to/radarimages/folder'
SAVE_IMAGES = False #save downsampled images to the directory above. This must be manually created

COLLECTOR_DATA_FILE = 'weather_data.json'

#number of samples to use for prediction (> 1)
NO_SAMPLES = 2

#code for smn measurement location
SMN_CODE = 'BER'

#get termperature
GET_TEMPERATURE = True

#Twitter
########

#update messages used for twitter
RAIN_MESSAGES = ["S'schifft.", "Es schifft.", "Es rägnet.", "S'rägnet.", "Räge Rägetröpfli...", "Wieder eis nass.", "Nassi Sach dusse."]
NO_RAIN_MESSAGES = ["S'schifft nümme.", "Es schifft nümme.", "Es rägnet nümme.", "S'rägnet nümme.", "Es isch wieder troche."]
SNOW_MESSAGES = ["S'schneit.", "Es schneit.", "Wieder eis Schnee.", "Es schneielet.", "S'schneielet"]
NO_SNOW_MESSAGES = ["S'schneit nümme.", "Es schneit nümme.", "Wieder troche.", "Es isch wieder troche"]

CONSUMER_KEY='consumer-key'
CONSUMER_SECRET='consumer-secret'
ACCESS_TOKEN='access-token'
ACCESS_TOKEN_SECRET='token-secret'

TWEET_STATUS = False
TWEET_PREDICTION = False


#Server stuff
#############
SERVER_DATA_FILE = './server/server_data.json'
UPDATE_PATH = '/someupdateurl'

WEATHER_UPDATE_PATH = '/someurl_weather'
SERVER_WEATHER_URL = '%s%s'%(SERVER, WEATHER_UPDATE_PATH)

SERVER_URL = 'http://127.0.0.1:5000%s'%UPDATE_PATH
SECRET = 'secret'
DUNNO_MESSAGE = u'Weiss nümme'
DISPLAY_DATE_FORMAT = '%d.%m.%Y %H:%M'

USE_MONGODB = False
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017

SERVER_RAIN_MESSAGE = "S'schifft"
SERVER_NO_RAIN_MESSAGE = "S'isch troche"
SERVER_SNOW_MESSAGE = "S'schneit"
SERVER_RAIN_SINCE_MESSAGE = "S'schifft sit"
SERVER_SNOW_SINCE_MESSAGE = "S'isch troche sit"
SERVER_DRY_SINCE_MESSAGE = "S'schneit sit"

