# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # FIXME

import settings
from rain import Measurement, build_timestamp, get_prediction_data, AmbientDataFetcher
from utils import tweet_status
from weatherchecks import does_it_snow, does_it_rain
from datastorage import DataStorage
import json
# from json import encoder
import requests
from datetime import datetime, timedelta
import copy


# FIXME: move parts to own module/class
def schiffts():
    # some initialization
    old_data = {}
    data_queue = []
    current_data = None
    next_hit = {}
    last_update = ''

    intensity = 0
    temperature_data = {'status': 0}

    storage = DataStorage(settings.COLLECTOR_DATA_FILE)

    # get date
    now = datetime.now()
    latest_radar = now - timedelta(0, 10*60)     # radar has a 8minute-ish delay, so go 10minutes back in time
    timestamp = build_timestamp(latest_radar)

    if settings.DEBUG:
        print "current timestamp: %s"%timestamp

    old_rain, old_last_rain, old_last_dry, old_snow, old_data_queue, old_location_weather = storage.load_data()

    # get data from srf.ch up to now
    for minutes in range(0, settings.NO_SAMPLES+3):
        timestamp = build_timestamp(latest_radar - timedelta(0, 60*5*minutes))
        # try to retrieve a measurement for the timestamp from the old data queue
        old_measurement = next((item for item in old_data_queue if item.timestamp == timestamp), None)

        # get a new measurement from srf.ch if it wasn't found in the old data queue
        if not old_measurement:
            # try:
                measurement = Measurement((settings.X_LOCATION, settings.Y_LOCATION), timestamp, 1, 105)
                data_queue.append(measurement)
                if settings.DEBUG:
                    print "add sample with timestamp %s"%timestamp

                if minutes == 0:
                    current_data = measurement
                    last_update = timestamp

            # except Exception, e:
            #     print "fail in queuefiller: %s" % e

        # use old data
        else:
            if settings.DEBUG:
                print "%s already in queue" % timestamp

            if minutes == 0:
                current_data = old_measurement
                last_update = timestamp

            data_queue.append(old_measurement)

        if len(data_queue) == settings.NO_SAMPLES:
            break

    queue_to_save = copy.deepcopy(data_queue)

    # only calculate next rain if it is currently not raining at the current location
    if does_it_rain(current_data):
        rain_now = True
        last_rain = current_data.timestamp
        last_dry = old_last_dry
        intensity = current_data.location['intensity']

    else:
        rain_now = False
        last_dry = current_data.timestamp
        last_rain = old_last_rain

        next_hit = get_prediction_data(current_data, data_queue, old_data, settings.TWEET_PREDICTION)

    if settings.DEBUG:
        print "raining now: %s, raining before: %s" % (rain_now, old_rain)

    # get temperature info from SMN
    if settings.GET_TEMPERATURE:
        temperature_data['status'], temperature_data['temperature'] = AmbientDataFetcher.get_temperature(settings.SMN_CODE)
        if settings.DEBUG:
            print "temperature data: %s" % temperature_data

    # get current weather from smn (only if the latest value is older than 30min)
    if old_location_weather != {} and 'timestamp' in old_location_weather:
        if now - datetime.strptime(str(old_location_weather['timestamp']), settings.DATE_FORMAT) > timedelta(0,60*30):
            location_weather = AmbientDataFetcher.get_weather(settings.SMN_CODE)
        else:
            location_weather = old_location_weather
    else:
        location_weather = AmbientDataFetcher.get_weather(settings.SMN_CODE)

    # check for snow
    snow = does_it_snow(intensity, temperature_data)

    # update twitter if state changed
    if rain_now != old_rain and settings.TWEET_STATUS:
        snow_update = snow or old_snow
        tweet_status(rain_now, snow_update)

    storage.save_data(last_update, queue_to_save, rain_now, last_dry, last_rain, next_hit, intensity, snow,
                      location_weather)

    # make data
    data_to_send = {'prediction': next_hit, 'current_data': current_data.location, 'temperature': temperature_data,
                    'snow': snow, 'current_weather': location_weather}

    # send data to server
    # encoder.FLOAT_REPR = lambda o: format(o, '.2f')
    payload = {'secret': settings.SECRET, 'data': json.dumps(data_to_send)}
    if settings.DEBUG:
        print "data for server: %s"%payload
    try:
        r = requests.post(settings.SERVER_URL, data=payload)
        print r.text
    except Exception, e:
        print e

if __name__ == '__main__':
    # schiffts()
    from rain import get_rain_info
    print get_rain_info(105, settings.NO_SAMPLES)
