# -*- coding: utf-8 -*-

from flask import Flask, abort, request, render_template, Response
import dateutil.parser
from datetime import datetime
import json
import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)  #FIXME: only used for localhost
import settings


app = Flask(__name__)
app.config.from_object(__name__)


@app.route('/')
def index():
    """
    Display the webpage
    """

    last_dry = settings.DUNNO_MESSAGE
    last_rain = settings.DUNNO_MESSAGE
    rain_since = settings.DUNNO_MESSAGE
    dry_since = settings.DUNNO_MESSAGE
    last_update = None

    dt = None

    #read old data from file
    try:
        f = open(settings.SERVER_DATA_FILE, 'r')
        weather_data = json.loads(f.read())

        if weather_data['last_update_rain']:
            if weather_data.has_key('last_rain') and weather_data['last_rain']:
                last_update =  dateutil.parser.parse(weather_data['last_rain'])
                dt = datetime.now() - last_update
                rain = True

        else: 
            if weather_data.has_key('last_dry') and weather_data['last_dry']:
                last_update =  dateutil.parser.parse(weather_data['last_dry'])
                dt = datetime.now() - last_update
                rain = False 

        #format datetime for display
        if weather_data['last_dry']:
            last_dry = dateutil.parser.parse(weather_data['last_dry']).strftime(settings.DISPLAY_DATE_FORMAT)

        if weather_data['last_rain']:
            last_rain = dateutil.parser.parse(weather_data['last_rain']).strftime(settings.DISPLAY_DATE_FORMAT)

        if weather_data.has_key('rain_since') and weather_data['rain_since']:
            rain_since = dateutil.parser.parse(weather_data['rain_since']).strftime(settings.DISPLAY_DATE_FORMAT)          

        if weather_data.has_key('dry_since') and weather_data['dry_since']:
            dry_since = dateutil.parser.parse(weather_data['dry_since']).strftime(settings.DISPLAY_DATE_FORMAT)

    except Exception, e:
        rain = False
    
    return render_template('index.html', rain=rain, last_rain=last_rain, last_dry=last_dry, dry_since=dry_since, \
                            rain_since=rain_since, last_update=last_update)


@app.route(settings.UPDATE_PATH, methods=['POST'])
def update_weather():
    """
    Called by the rain updater
    """
    
    secret = request.form['secret']

    #verify password and check if data is present
    if(secret == settings.SECRET and not request.form['data'] == None):

        #read last saved data, if it fails set default values
        try:
            f = open(settings.SERVER_DATA_FILE, 'r')
            weather_data = json.loads(f.read())
        except Exception, e:
            weather_data = {'last_rain_intensity':None,
                            'last_rain':None,
                            'last_dry':None,
                            'rain_since':None,
                            'dry_since':None,
                            'last_update_rain':False,
                            }
        
        try:
            data = json.loads(request.form['data'])
            now = datetime.now().isoformat()

            #update weather_data, if necessary
            #update contains rain
            if data.has_key('intensity'):
                weather_data['last_rain_intensity'] = data['intensity']

                if weather_data.has_key('last_update_rain'):
                    if weather_data['last_update_rain'] == False or weather_data['rain_since'] == None:
                        weather_data['rain_since'] = now
                else:
                    weather_data['rain_since'] = now


                weather_data['last_rain'] = now
                weather_data['last_update_rain'] = True    

            #update contains no rain
            else:

                if weather_data.has_key('last_update_rain'):
                    if weather_data['last_update_rain'] == True or weather_data['dry_since'] == None:
                        weather_data['dry_since'] = now 

                else:
                    weather_data['dry_since'] = now

                weather_data['last_dry'] = now
                weather_data['last_update_rain'] = False

            with open(settings.SERVER_DATA_FILE, 'w') as outfile:
                json.dump(weather_data, outfile)

        except Exception, e:
            return "fail: %s"%e

        return 'merci'
        
    else:
       abort(401)


@app.route('/api/schiffts')
def api():
        #read last saved data, if it fails return an error
        #FIXME: let the webserver return the file, so that flask won't serve the file
        try:
            f = open(settings.SERVER_DATA_FILE, 'r')
            weather_raw = f.read()
        except Exception, e:
            weather_data = {'last_rain_intensity':None,
                            'last_rain':None,
                            'last_dry':None,
                            'rain_since':None,
                            'dry_since':None,
                            'last_update_rain':False,
                            }
            weather_raw = json.dumps(weather_data)

        response_content = weather_raw
        response = Response(response=response_content, status=200, mimetype="application/json")
        return response


if __name__ == '__main__':
    app.run()
    