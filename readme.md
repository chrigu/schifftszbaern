#Schiffts z'Bärn

*Still under construction and still quite messy*

##Introduction

"Schiffts z'Bärn" (is it raining in Berne) is a serivce that broadcasts (over Twitter and/or a webpage) if it is currently raining in Berne, Switzerland (the service can be configured for other locations in Switzerland too). With some additional hardware it is also possible to display rain warnings on a ambient device (light cloud).

The rain information is pulled from the [Swiss National TV's rain radar webpage (SRF)](http://www.srf.ch/meteo/radar). On this website the rain is displayed as an overlay on a map. The overlay is just a PNG where colored pixels represent rain cells and this information is used as the data source.

##Quickstart for the impatient
1. Install the required Pyhton packages via `pip install -r requirements/base.txt`
2. Run `cp settings.sample.py settings.py`
3. Run `python main.py`
5. On the terminal you should see some output, but it should state somewhere "raining now: True/False"

##Setup

###Requirements

Python 2.7 with the following libraries (some are quite a pita to install.....)

* SciPy
* NumPy
* PIL
* pypng
* python_twitter
* Flask (only for website)
* Dateutil (only for website)
* Requests
* PyMongo (only if you use the weather crawler)
* LXML (only if you use the weather crawler)

###Configure for your location

In order to configure the service for other locations in Switzerland you need to get the location's position on the overlay PNG. And this is the tricky part.

The easiest approach is to identify a rain formation on SRF's rain radar that is just over your desired location for a given time say 15:00 (You need to do that on the their website as there's the map below the overlay with all geographic information). After that, download the PNG from the website (look out for files like http://www.srfcdn.ch/meteo/nsradar/media/web/PPIMERCATOR.20140722150000.png in your browser's Web Inspector) for the time you chose and open it somewhere where you can measure the pixels. Try to find the rain formation that you identified earlier again on the downloaded PNG. When you find it you just have to measure the x-pixels (from the left edge) and the y-pixels (trom the top edge). This is your locations position that you need to change in the settings. Easy, right?

Berne's location is 364/366 and Lausanne's 306/416 (x/y).

###Twitter Setup

To enable Twitter updates there are 2 things that need to be done:

1. Setup a twitter app and obtain the corresponding consumer & consumer secret.
2. Obtain a token & token secret for the twitter account you'd like to use.

####Consumer & Consumer Secret

Setup & register a [twitter app](https://apps.twitter.com/app/new) with write permissions. The consumer key and secret can be accessed from Twitter's website.

####Token & Token Secret

You can run `python get_token.py` (requires the oauth2 package) and it will take you through the process of creating a token and token secret.

####Weather Data

*beta*

Currently it can be configured that the services fetches the current weather information about Berne (for the time being only this location). The information contains the current situation (rain, fog, ...) and the temperature. This feature requires a MongoDB on the server side.

You need to install the required packages with `pip install -r requirements/weather_fetcher.txt`

The weather information is fetched from the [Federal Office of Meteorology and Climatology MeteoSwiss'](http://www.sma.ch) website. The weather is updated every 30 minutes.

####Temperature Data
The [Federal Office of Meteorology and Climatology MeteoSwiss'](http://www.sma.ch) offers an API where weather information from different measurement stations is made available. Currently only the temperature information is used. More information about the topic can be found the [OpenData SMN page](http://data.netcetera.com/smn/). The temperature information from this API will be used instead of the SMA website crawling.

##Server Setup

The server is based on flask so please refer to flask's [documentation](http://flask.pocoo.org/docs/quickstart/#deploying-to-a-web-server) for configuring it with your webserver. For testing you can run flask locally. The only setting that is required is the `SERVER_DATA_FILE` as the server saves the latest data to it. The path of this file can be absolute or relative (the default value is relative so you need to run `python server/server.py` from the main directory).

##Configuration Options

The configuration can be found in settings.py. The following settings are available:

| Setting        | Type           | Description  |
| ------------- |-----------------| ------------|
| DEBUG      | Boolean | If set to true additional information for debugging is displayed |
| DATE_FORMAT      |   Date format   |  Default `%Y%m%d%H%M00`. This format is used by srf.ch to name the png files. So don't change it unless you know what you're going to do |
| X_LOCATION  |   Int      |   x-position on the radar png for your location |
| Y_LOCATION  |   Int      |   y-position on the radar png for your location |
| RADAR_IMAGES  |   String      |   Folder to save the downsampled radar images to. This folder must be manually created.|
| SAVE_IMAGES  |   Boolean      |   If set true the downsampled radar images are saved to the RADAR_IMAGES folder|
| COLLECTOR_DATA_FILE  |   String      |   Name of the file where the latest data is saved. Will be saved in the root directory.|
| NO_SAMPLES  |   Int      |   Number of radar images to use for rain prediction.|
| SMN_CODE  |   String      |   Code of closest [measurement station for temperature](http://data.netcetera.com/smn/swagger)|
| GET_TEMPERATURE  |   String      |   Get temperature info from SMN stations |
| RAIN_MESSAGES  |   List      |   Messages to indicate rain. Please add several as twitter does not allow posting duplicate messages.|
| NO_RAIN_MESSAGES  |   List      |   Messages to indicate end of rain. Please add several as twitter does not allow posting duplicate messages.|
| SNOW_MESSAGES  |   List      |   Messages to indicate snowfall. Please add several as twitter does not allow posting duplicate messages.|
| NO_SNOW_MESSAGES  |   List      |   Messages to indicate end of snowfall. Please add several as twitter does not allow posting duplicate messages.|
| CONSUMER_KEY  |   String      |   Consumer key for twitter app|
| CONSUMER_SECRET  |   String      |   Consumer secret for twitter app|
| ACCESS_TOKEN  |   String      |   Access token for your twitter account|
| ACCESS_TOKEN_SECRET  |   String      |   Token secret for your twitter account|
| TWEET_STATUS  |   Boolean      |   Tweet if it starts or stops raining|
| TWEET_PREDICTION  |   Boolean      |    Tweet rain prediction|
| SERVER_DATA_FILE | String | Path to the file where the server's data should be stored |
| UPDATE_PATH | String | Path on the weberver where the updates will be sent |
| SERVER_URL | String | URL where the updates will be sent to |
| SECRET | String | Secret required for sending updates to the server |
| DUNNO_MESSAGE | String | Message to display when no data is available |
| DISPLAY_DATE_FORMAT | Date format | Format used to display the date on the website. Default `%d.%m.%Y %H:%M` |
| SERVER_DATA_FILE | String | Path to the server's JSON file |
| WEATHER_UPDATE_PATH | String | URL where the weather updates will be sent to (very beta) |
| USE_MONGODB | Boolean | Use MongoDB for weather data storage (beta) |
| MONGODB_HOST | String | MongoDB host |
| MONGODB_PORT | Integer | MongoDB's port |
| SERVER_RAIN_MESSAGE | String | Message to indicate rain on the webpage |
| SERVER_RAIN_MESSAGE | String | Message to indicate rain on the webpage |
| SERVER_NO_RAIN_MESSAGE | String | Message to indicate no rain on the webpage |
| SERVER_SNOW_MESSAGE | String | Message to indicate snowfall on the webpage |
| SERVER_RAIN_SINCE_MESSAGE | String | "Rain since" message |
| SERVER_SNOW_SINCE_MESSAGE | String | "Snow since" message |
| SERVER_DRY_SINCE_MESSAGE | String | "Dry" message |

##Light cloud
The light cloud is an Espruino with a WLAN module that starts to blink when rain cells are approaching the location. The blinking's frequency increases when the cell get closer to the location.

###Requirements
* [Espruino](http://www.espruino.com/) (Pico is recommended)
* [ESP8622 Wifi module](http://www.espruino.com/ESP8266) (v0.25 required)
* [NeoPixel LED](http://www.adafruit.com/category/168)

Instead of the ESP8622 a [CC3000](http://www.espruino.com/CC3000) can be used as WLAN module. Keep in mind as this module is bigger and requires more connections from the Espruino. 

The old unstable Arduino code can be found in hardware/old/arduino

###Wiring

| Espruino Pin        | Component           | Pin  |
|---------------------|---------------------|------|
| GND  | ESP8266 |  GND |
| 3.3 | ESP8266 | VCC |
| 3.3 | ESP8266 | CH_PD |
| A2 | ESP8266 | URXD |
| A3 | ESP8266 | UTXD |
| GND | NeoPixel | GND |
| B15 | NeoPixel | Din |
| Vbat | NeoPixel | Vin |


###Code
In the code you only need to change the the WLAN settings to get things working (in hardware/schiffts.js (ssid / password).

##Tests
Some basic tests can be run from the main directory. You can run `python tests.py` to test the part that analyzes the radar's data. To the test the server part run `python server/server_tests.py`.

##Todo

* Clean code & hierarchy
* Documentation (obviously)
* 1 config file for everything
* remove magic numbers
* Clean up SVG classes & attributes
* add a night class (no sun at night)
* use scss
* add testfile for light cloud
* Refactor tests
* Move test to own directory
* Move some weather analysis to own module
