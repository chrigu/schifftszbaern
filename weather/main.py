# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # FIXME

import settings
from rain import build_timestamp, AmbientDataFetcher
from rain.utils import tweet_status, tweet_prediction
from weatherchecks import does_it_snow, does_it_rain
from datastorage import DataStorage
import json
# from json import encoder
import requests
from datetime import datetime, timedelta
import copy
from rain import get_rain_info


# FIXME: move all to weather
def schiffts():
    # some initialization
    old_data = {}
    prediction_id = ''

    intensity = 0
    temperature_data = {'status': 0}

    storage = DataStorage(settings.COLLECTOR_DATA_FILE)

    # get date
    now = datetime.now()
    latest_radar = now - timedelta(0, 10*60) # radar has a 8minute-ish delay, so go 10minutes back in time
    timestamp = build_timestamp(latest_radar)

    if settings.DEBUG:
        print "current timestamp: %s"%timestamp

    stored_data = storage.load_data()

    measurements, next_hit = get_rain_info(settings.X_LOCATION, settings.Y_LOCATION, 105, settings.NO_SAMPLES)
    current_measurement = measurements[0]

    current_data_at_position = current_measurement.rain_at_position(52, 52)
    timestamp = current_measurement.timestamp

    queue_to_save = copy.deepcopy(measurements)

    # only calculate next rain if it is currently not raining at the current location
    if does_it_rain(current_data_at_position):
        rain_now = True
        last_rain = current_measurement.timestamp
        last_dry = stored_data['old_last_dry']
        intensity = current_data_at_position['intensity']

    else:
        rain_now = False
        last_dry = current_measurement.timestamp
        last_rain = stored_data['old_last_rain']

        if next_hit and settings.TWEET_PREDICTION:
            try:
                # don't send prediction if there's an old next hit value
                if ('next_hit' in old_data and not old_data['next_hit']) and not stored_data['old_prediction_id']:
                    tweet_prediction(next_hit)
                    prediction_id = next_hit['id']

            except Exception, e:
                print e
                pass

    if settings.DEBUG:
        print "raining now: %s, raining before: %s" % (rain_now, stored_data['old_rain'])

    # get temperature info from SMN
    if settings.GET_TEMPERATURE:
        temperature_data['status'], temperature_data['temperature'] = AmbientDataFetcher.get_temperature(settings.SMN_CODE)
        if settings.DEBUG:
            print "temperature data: %s" % temperature_data

    # get current weather from smn (only if the latest value is older than 30min)
    if stored_data['old_weather_data'] != {} and 'timestamp' in stored_data['old_weather_data']:
        if now - datetime.strptime(str(stored_data['old_location_weather']['timestamp']), settings.DATE_FORMAT) > timedelta(0, 60*30):
            location_weather = AmbientDataFetcher.get_weather(settings.SMN_CODE)
        else:
            location_weather = stored_data['old_location_weather']
    else:
        location_weather = AmbientDataFetcher.get_weather(settings.SMN_CODE)

    # check for snow
    snow = does_it_snow(intensity, temperature_data)

    # update twitter if state changed
    if rain_now != stored_data['old_rain'] and settings.TWEET_STATUS:
        snow_update = snow or stored_data['old_snow']
        tweet_status(rain_now, snow_update)

    storage.save_data(timestamp, queue_to_save, rain_now, last_dry, last_rain, next_hit, intensity, snow,
                      location_weather, prediction_id)

    # make data
    data_to_send = {'prediction': next_hit, 'current_data': current_data_at_position, 'temperature': temperature_data,
                    'snow': snow, 'current_weather': location_weather}

    # send data to server
    # encoder.FLOAT_REPR = lambda o: format(o, '.2f')
    payload = {'secret': settings.SECRET, 'data': json.dumps(data_to_send)}
    if settings.DEBUG:
        print "data for server: %s" % payload
    try:
        r = requests.post(settings.SERVER_URL, data=payload)
        print r.text
    except Exception, e:
        print e

if __name__ == '__main__':
    schiffts()

