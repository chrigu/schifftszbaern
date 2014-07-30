# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #FIXME

import settings
from rain import Measurement, build_timestamp, RainPredictor
from utils import tweet_status

import time
import json
import requests
from datetime import datetime, timedelta
from time import mktime
import copy


def encode(obj):
    """
    Encodes the Measurement object so that it can be saved as JSON
    FIXME: Move elsewhere
    """   
    if isinstance(obj, Measurement):
        return {'data':obj.data, 'timestamp':datetime.strftime(obj.timestamp, settings.DATE_FORMAT)}
    return obj


def schiffts():
    #some initialization
    old_data_queue = []
    data_queue = []
    current_data = None
    old_latest_data = None
    forecast_now_data = None
    last_update = ''
    old_rain = False
    old_last_rain = None
    old_last_dry = None
    last_rain = None
    last_dry = None
    next_hit = {}

    #get date
    now = datetime.now()
    latest_radar = now - timedelta(0, 10*60)     #radar has a 8minute-ish delay, so go 10minutes back in time
    timestamp = build_timestamp(latest_radar)

    if settings.DEBUG:
        print "current timestamp: %s"%timestamp

    #try to open the file with the old data
    try:
        f = open(settings.COLLECTOR_DATA_FILE, 'r')

        old_data = json.loads(f.read())

        #check if old data was saved, if yes create measurement objects and add them to a queue
        if old_data.has_key('queue'):
            for old_values in old_data['queue']:
                measurement = Measurement.from_json((settings.X_LOCATION, settings.Y_LOCATION), 3, 105, old_values)
                if measurement:
                    old_data_queue.append(measurement)

        #get the rest of the old data (last time of no-/rain, etc.)
        if old_data.has_key('last_sample_rain'):
            old_rain = old_data['last_sample_rain']
        if old_data.has_key('last_rain'):
            old_last_rain = datetime.strptime(old_data['last_rain'],settings.DATE_FORMAT)
        if old_data.has_key('last_dry'):
            old_last_dry = datetime.strptime(old_data['last_dry'],settings.DATE_FORMAT)
        if old_data.has_key('next_hit'):
            old_next_hit = datetime.strptime(old_data['old_next_hit'],settings.DATE_FORMAT)

        last_update = None

    except Exception, e:
        print e

    #get data from srf.ch up to now
    for minutes in range(0,settings.NO_SAMPLES+3):
        timestamp = build_timestamp(latest_radar - timedelta(0,60*5*minutes))
        #try to retrieve a measurement for the timestamp from the old data queue
        old_measurement = next((item for item in old_data_queue if item.timestamp == timestamp), None)
        
        #get a new measurement from srf.ch if it wasn't found in the old data queue
        if not old_measurement:
            try:
                measurement = Measurement((settings.X_LOCATION, settings.Y_LOCATION), timestamp, 3, 105)
                measurement.analyze_image()
                data_queue.append(measurement)
                if settings.DEBUG:
                    print "add sample with timestamp %s"%timestamp

                if minutes == 0:
                    current_data = measurement

            except Exception, e:
                print "fail in queuefiller: %s"%e
                
        #use old data
        else:
            if settings.DEBUG:
                print "%s already in queue"%timestamp

            if minutes == 0:
                current_data = old_measurement

            data_queue.append(old_measurement)


        if len(data_queue) == settings.NO_SAMPLES:
            break

    queue_to_save = copy.deepcopy(data_queue)

    #only calculate next rain if it is currently not raining at the current location
    if current_data.location and current_data.location.has_key('intensity'):
        rain_now = True
        last_rain = current_data.timestamp
        last_dry = old_last_dry

    else:
        rain_now = False
        last_dry = current_data.timestamp
        last_rain = old_last_rain

        #make prediction. Very much beta
        if current_data:
            predictor = RainPredictor(data_queue, current_data.timestamp, 18)
            try:
                time_delta, size, impact_time = predictor.make_forecast()
                if settings.DEBUG:
                    print "next rain at %s (delta %s) with size %s"%(impact_time, int(time_delta), size)

                next_hit['time_delta'] = time_delta
                next_hit['size'] = size
                next_hit['time'] = datetime.strftime(impact_time, settings.DATE_FORMAT)


            except Exception, e:
                time_delta = None

    if settings.DEBUG:
        print "raining now: %s, raining before: %s"%(rain_now, old_rain)

    #update twitter if state changed
    if rain_now != old_rain and settings.TWEET_STATUS:
        tweet_status(rain_now)


    #save data, convert datetime objects to strings
    if last_dry:
        last_dry_string = datetime.strftime(last_dry, settings.DATE_FORMAT)
    else:
        last_dry_string = None

    if last_rain:
        last_rain_string = datetime.strftime(last_rain, settings.DATE_FORMAT)
    else:
        last_rain_string = None

    #save data to file
    save_data = {'last_update':last_update, 'queue':queue_to_save, 'last_sample_rain':rain_now, 'last_dry':last_dry_string, \
                'last_rain':last_rain_string, 'next_hit':next_hit}

    with open(settings.COLLECTOR_DATA_FILE, 'w') as outfile:
        json.dump(save_data, outfile, default=encode)

    #send data to server
    payload = {'secret':settings.SECRET, 'data':json.dumps(current_data.location)}
    if settings.DEBUG:
        print "data for server: %s"%payload
    try:
        r = requests.post(settings.SERVER_URL, data=payload)
        print r.text
    except Exception, e:
        print e

if __name__ == '__main__':
    schiffts()

