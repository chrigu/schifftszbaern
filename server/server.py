# -*- coding: utf-8 -*-

from flask import Flask, abort, request, render_template, Response
import dateutil.parser
from datetime import datetime
import json
import os

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)  # FIXME: only used for localhost
import settings

"""

1 = sunny
101 = clear sky
2 = mostly sunny, some clouds
102 = mostly clear sky, some clouds
35 = overcast and dry
3 = partly sunny, thick passing clouds
4 = overcast
14 = very cloudy, light rain
5 = very cloudy
21 = very overcast with frequent sleet
6 = sunny intervals,  isolated showers
15 = very cloudy, light sleet
16 = very cloudy, light snow
17 = very cloudy, rain
18 = very cloudy, rain & snow
19 = very cloudy, snow
20 = very overcast with rain
22 = very overcast with heavy snow
23, 24 = thunderstomrs
25 = thunderstomrs & heavy rain
29 = Sunny intervals, scattered showers
7, 10 = sunny intervals, showers & snow, sleet
8, 11 = sunny intervals,  snow showers
9 = sunny intervals, showers
12 = cloudy with thunder (light & sun)
13 = cloudy with thunder (sun, rain)
26 = sunny with high clouds
27 = fog sunny above
28 = foggy
30 = light clouds some snow, partly sunny
31 = light clouds some snow & rain, partly sunny
32 = light clouds some rain, partly sunny
33 = clouds rain, partly sunny
34 = clouds some snow, partly sunny

"""

app = Flask(__name__, static_url_path='')
app.config.from_object(__name__)

app.config.update(dict(
    DATA_FILE=settings.SERVER_DATA_FILE,
    DUNNO_MESSAGE=settings.DUNNO_MESSAGE,
    DRY_MESSAGE=settings.SERVER_DRY_MESSAGE,
    DRY_SINCE_MESSAGE=settings.SERVER_DRY_SINCE_MESSAGE,
    RAIN_MESSAGE=settings.SERVER_RAIN_MESSAGE,
    RAIN_SINCE_MESSAGE=settings.SERVER_RAIN_SINCE_MESSAGE,
    SNOW_MESSAGE=settings.SERVER_SNOW_MESSAGE,
    SNOW_SINCE_MESSAGE=settings.SERVER_SNOW_SINCE_MESSAGE,
    RAIN_UPDATE_PATH=settings.RAIN_UPDATE_PATH,
    WEATHER_UPDATE_PATH=settings.WEATHER_UPDATE_PATH,
    SECRET=settings.SECRET,
    DISPLAY_DATE_FORMAT=settings.DISPLAY_DATE_FORMAT
))

if settings.USE_MONGODB:
    # connect to mongodb
    import pymongo
    connection = pymongo.Connection(settings.MONGODB_HOST, settings.MONGODB_PORT)
    db = connection.schiffts


def read_from_file(raw=False):
    # read last saved data, if it fails set default values
    try:
        f = open(app.config['DATA_FILE'], 'r')
        weather_data = f.read()
        if not raw:
            weather_data = json.loads(weather_data)

    except Exception, e:
        weather_data = {'last_rain_intensity':None,
                        'last_rain':None,
                        'last_dry':None,
                        'rain_since':None,
                        'dry_since':None,
                        'last_update_rain':False,
                        'weather_symbol_id': -1
                        }

        if raw:
            weather_data = json.dumps(weather_data)

    return weather_data


def check_password(form):
    try:
        secret = form['secret']
        # verify password and check if data is present
        if secret == app.config['SECRET'] and not form['data'] is None:
            return True
    except Exception, e:
        pass

    return False


@app.route('/', methods=['GET'])
def index():
    """
    Display the webpage
    """

    last_dry = app.config['DUNNO_MESSAGE']
    last_rain = app.config['DUNNO_MESSAGE']
    rain_since = app.config['DUNNO_MESSAGE']
    dry_since = app.config['DUNNO_MESSAGE']
    situation_message = app.config['DRY_MESSAGE']
    since_message = app.config['DRY_SINCE_MESSAGE']
    last_update = None
    snow = False
    body_classes = ""

    # read old data from file
    try:
        f = open(app.config['DATA_FILE'], 'r')
        weather_data = json.loads(f.read())

        if weather_data.has_key('snow') and weather_data['snow']:
            snow = weather_data['snow']

        if weather_data['last_update_rain']:
            if weather_data.has_key('last_rain') and weather_data['last_rain']:
                last_update =  dateutil.parser.parse(weather_data['last_rain'])
                dt = datetime.now() - last_update
                rain = True
                if snow:
                    situation_message = app.config['SNOW_MESSAGE']
                    since_message = app.config['SNOW_SINCE_MESSAGE']
                else:
                    situation_message = app.config['RAIN_MESSAGE']
                    since_message = app.config['RAIN_SINCE_MESSAGE']

        else: 
            if weather_data.has_key('last_dry') and weather_data['last_dry']:
                last_update =  dateutil.parser.parse(weather_data['last_dry'])
                # dt = datetime.now() - last_update
                rain = False 

        # format datetime for display
        if weather_data['last_dry']:
            last_dry = dateutil.parser.parse(weather_data['last_dry']).strftime(app.config['DISPLAY_DATE_FORMAT'])

        if weather_data['last_rain']:
            last_rain = dateutil.parser.parse(weather_data['last_rain']).strftime(app.config['DISPLAY_DATE_FORMAT'])

        if weather_data.has_key('rain_since') and weather_data['rain_since']:
            rain_since = dateutil.parser.parse(weather_data['rain_since']).strftime(app.config['DISPLAY_DATE_FORMAT'])          

        if weather_data.has_key('dry_since') and weather_data['dry_since']:
            dry_since = dateutil.parser.parse(weather_data['dry_since']).strftime(app.config['DISPLAY_DATE_FORMAT'])

    except Exception, e:
        rain = False

    # if GET parameter is present, overwrite weather variables
    weather = request.args.get('weather', '')

    if weather == 'rain':
        rain = True
        snow = False
    elif weather == 'snow':
        rain = True
        snow = True
    elif weather == 'sun':
        rain = False
        snow = False

    # get latest weather data
    try:
        latest_sample = db.weather_samples.find().sort('time', pymongo.DESCENDING)[0]

        # only display weather if the latest value is not older than 1h
        time_diff = datetime.utcnow() - latest_sample['time']
        time_diff_minutes = time_diff.days * 1440 + time_diff.seconds # py 2.6 :-/ use time_diff.total_seconds() in 2.7
        if time_diff_minutes < 60*60:
            # replace strings in weather attributes and concate them
            for attribute in latest_sample['weather']:
                attribute = attribute.replace(" ", "-")
                body_classes += "%s "%attribute

        body_classes = body_classes.strip()

    except Exception, e:
        body_classes = "no-weather-data"

    # add additional classes to the body
    if body_classes == "":
        body_classes = "no-weather-data"

    if rain:
        body_classes += " rain"
    else:
        body_classes += " no-rain"

    if snow:
        body_classes += " snow"

    # add non-rain/snow related info to body class
    """
    sunny           1, 26
    overcast        35, 4, 21, 20, 22
    partly cloudy   2, 3, 6, 29, 7, 10, 8, 11, 9, 30, 31, 32, 33, 34
    cloudy          14, 5, 15, 16, 17, 19, 18
    light rain      21, 6, 15, 18, 29, 7, 10, 9, 31, 32, 33
    heavy rain      17, 20, 26
    light snow      14, 21, 15, 16, 18, 7, 10, 30, 31, 34
    heavy snow      19, 22, 8, 11
    fog             27, 28
    thunderstorms   23, 24, 25, 12, 13

    states > 100 are night states
    """
    if weather_data.has_key('weather_symbol_id') and weather_data['weather_symbol_id'] != -1:
        if weather_data['weather_symbol_id'] > 100:
            weather_symbol_id = weather_data['weather_symbol_id'] - 100
            body_classes += " night"
        else:
            weather_symbol_id = weather_data['weather_symbol_id']

        if weather_symbol_id in [35, 4, 21, 20, 22]:
            body_classes += " overcast"
        elif weather_symbol_id in [2, 3, 6, 29, 7, 10, 8, 11, 9, 30, 31, 32, 33, 34]:
            body_classes += " partly-cloudy"
        elif weather_symbol_id in [14, 5, 15, 16, 17, 19, 18]:
            body_classes += " cloudy"
        elif weather_symbol_id in [27, 28]:
            body_classes += " fog"
        elif weather_symbol_id in [23, 24, 25, 12, 13]:
            body_classes += " thunderstorms"

    return render_template('index.html', situation_message=situation_message, since_message=since_message, last_rain=last_rain, last_dry=last_dry, dry_since=dry_since, \
                            rain_since=rain_since, last_update=last_update, rain=rain, snow=snow, body_classes=body_classes)


@app.route(app.config['RAIN_UPDATE_PATH'], methods=['POST'])
def update_rain():
    """
    Called by the rain updater
    """
    
    if check_password(request.form):

        weather_data = read_from_file()
        
        try:
            data = json.loads(request.form['data'])
            now = datetime.now().isoformat()

            # update weather_data, if necessary
            # update contains rain
            if data.has_key('current_data'):
                if data['current_data'].has_key('intensity'):
                    weather_data['last_rain_intensity'] = data['current_data']['intensity']

                    if weather_data.has_key('last_update_rain'):
                        if weather_data['last_update_rain'] == False or weather_data['rain_since'] == None:
                            weather_data['rain_since'] = now
                    else:
                        weather_data['rain_since'] = now


                    weather_data['last_rain'] = now
                    weather_data['last_update_rain'] = True    

                # update contains no rain
                else:

                    if weather_data.has_key('last_update_rain'):
                        if weather_data['last_update_rain'] == True or weather_data['dry_since'] == None:
                            weather_data['dry_since'] = now 

                    else:
                        weather_data['dry_since'] = now

                    weather_data['last_dry'] = now
                    weather_data['last_update_rain'] = False

            if "prediction" in data:
                weather_data['prediction'] = data['prediction']

            if data.has_key('temperature') and data['temperature'].has_key('status') and data['temperature']['status'] == 200:
                if data['temperature'].has_key('temperature'):
                    weather_data['temperature'] = data['temperature']['temperature']

            if "snow" in data:
                weather_data['snow'] = data['snow']

            if data.has_key('current_weather') and data['current_weather'].has_key('weather_symbol_id'):
                weather_data['weather_symbol_id'] = data['current_weather']['weather_symbol_id']

            with open(app.config['DATA_FILE'], 'w') as outfile:
                json.dump(weather_data, outfile)

        except Exception, e:
            return "fail: %s"%e

        return "merci"
        
    else:
       abort(401)


# FIXME: use decorator
# @app.route(app.config['WEATHER_UPDATE_PATH'], methods=['POST'])
# def update_weather():
#     """
#     Called by the weather updater. Write data to db.
#     """
#     if settings.USE_MONGODB:
#         if check_password(request.form) and request.form.has_key('data'):
#             try:
#                 data = json.loads(request.form['data'])
#                 weather_samples = db.weather_samples
#                 now = datetime.utcnow()
            
#                 sample = {'weather': data['weather'], 'temperature':data['temperature'],
#                         'time': now}

#                 weather_samples.insert(sample)
#             except Exception, e:
#                 print e

#             return 'merci'
#         else:
#            abort(401)
#     else:
#         abort(401)


@app.route('/api/schiffts')
def api_current():
        # read last saved data, if it fails return an error
        # FIXME: let the webserver return the file, so that flask won't serve the file
        weather_raw = read_from_file(raw=True)

        response_content = weather_raw
        response = Response(response=response_content, status=200, mimetype="application/json")
        return response


@app.route('/api/chunntschoschiffe')
def api_forecast():
        # read last saved data, if it fails return an error
        # FIXME: let the webserver return the file, so that flask won't serve the file
        weather_data = read_from_file()

        if weather_data.has_key('prediction'):
            response_content = json.dumps(weather_data['prediction'])
        else:
            response_content = json.dumps({'prediction': {}})
        response = Response(response=response_content, status=200, mimetype="application/json")
        return response


@app.route('/test/chunntschoschiffe')
def api_test_forecast():
    return app.send_static_file('test_chunntschoschiffe.json')

if __name__ == '__main__':
    app.debug = settings.DEBUG
    app.run()
