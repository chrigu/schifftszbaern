# -*- coding: utf-8 -*-

import settings
import json
from datetime import datetime
from numpy import ndarray
from rain.Measurement import Measurement

class DataStorage(object):

    def __init__(self, filename):
        if filename:
            self.filename = filename
        else:
            return None

    def load_data(self):

        old_rain = False
        old_prediction_id = ''
        old_last_rain = None
        old_last_dry = None
        old_next_hit = None
        old_snow = False
        old_data_queue = []
        old_weather_data = {}

        #try to open the file with the old data
        try:
            f = open(self.filename, 'r')
            old_data = json.loads(f.read())
            # check if old data was saved, if yes create measurement objects and add them to a queue
            if 'queue' in old_data:
                for old_values in old_data['queue']:

                    measurement = Measurement.from_json(old_values['timestamp'], old_values['queue'],
                                                        old_values['location'], old_values['label_img'])
                    if measurement:
                        old_data_queue.append(measurement)

            #get the rest of the old data (last time of no-/rain, etc.)
            if 'last_sample_rain' in old_data:
                old_rain = old_data['last_sample_rain']
            if 'last_rain' in old_data and old_data['last_rain']:
                old_last_rain = datetime.strptime(old_data['last_rain'], settings.DATE_FORMAT)
            if 'last_dry' in old_data and old_data['last_dry']:
                old_last_dry = datetime.strptime(old_data['last_dry'], settings.DATE_FORMAT)
            if old_data.has_key('next_hit'):
                old_next_hit = datetime.strptime(old_data['old_next_hit'],settings.DATE_FORMAT)
            if 'last_sample_snow' in old_data:
                old_snow = old_data['last_sample_snow']
            if 'location_weather_data' in old_data:
                old_weather_data = old_data['location_weather_data']
            if 'next_hit' in old_data:
                old_next_hit = old_data['old_next_hit']
            if 'prediction_id' in old_data['prediction_id']:
                old_prediction_id = old_data['prediction_id']

        except Exception, e:
            if settings.DEBUG:
                print e

        finally:
            try:
                f.close()
            except:
                pass

        return {
            'old_rain': old_rain,
            'old_last_rain': old_last_rain,
            'old_last_dry': old_last_dry,
            'old_snow': old_snow,
            'old_data_queue': old_data_queue,
            'old_weather_data': old_weather_data,
            'old_next_hit': old_next_hit,
            'old_prediction_id': old_prediction_id
        }

    def save_data(self, last_update, queue_to_save, rain_now, last_dry, last_rain, next_hit, intensity,
                  snow, location_weather_data, prediction_id):
        #save data, convert datetime objects to strings
        try:
            if last_dry:
                last_dry_string = datetime.strftime(last_dry, settings.DATE_FORMAT)
            else:
                last_dry_string = None

            if last_rain:
                last_rain_string = datetime.strftime(last_rain, settings.DATE_FORMAT)
            else:
                last_rain_string = None

            #save data to file
            save_data = {'last_update': datetime.strftime(last_update, settings.DATE_FORMAT), 'queue': queue_to_save,
                         'last_sample_rain': rain_now, 'last_dry': last_dry_string,
                        'last_rain': last_rain_string, 'next_hit': next_hit, 'intensity': intensity,
                         'last_sample_snow': snow, 'location_weather_data': location_weather_data,
                         'prediction_id': prediction_id}

            with open(self.filename, 'w') as outfile:
                json.dump(save_data, outfile, default=self.encode)

            return True

        except Exception, e:
            if settings.DEBUG:
                print e

        return False

    @staticmethod
    def encode(obj):
        """
        Encodes the Measurement object so that it can be saved as JSON
        FIXME: Move elsewhere
        """
        if isinstance(obj, Measurement):
            # return {'data': obj.data, 'timestamp': datetime.strftime(obj.timestamp, settings.DATE_FORMAT)}
            try:
                return obj.to_dict()
            except Exception, e:
                print e
        elif isinstance(obj, ndarray):
            try:
                return obj.tolist()
            except Exception, e:
                return obj
        return obj


