# -*- coding: utf-8 -*-
import settings

from datetime import datetime, timedelta
import png

from utils import extrapolate_rain
from numpy import array as np_array
from Measurement import Measurement
from RadarImage import RadarImage
from RainPredictor2 import RainPredictor2
from AmbientDataFetcher import AmbientDataFetcher
from utils import get_timestring, calculate_movement


def get_rain_info(x, y, test_field_size, no_samples):

        # get date
        data_queue = []
        now = datetime.now()
        next_hit = None
        latest_radar = now - timedelta(0, 10*60)     # radar has a 8minute-ish delay, so go 10minutes back in time

        # get data from srf.ch up to now
        for minutes in range(0, no_samples+2):
            timestamp = build_timestamp(latest_radar - timedelta(0, 60*5*minutes))

            # try:
            # todo catch error

            radar_image = RadarImage((x-52, y-52, x+52, y+52), timestamp=timestamp)

            measurement = Measurement(radar_image, timestamp)
            #todo: rename .location
            if not measurement.location:

                data_queue.append(measurement)
                if settings.DEBUG:
                    print "add sample with timestamp %s" % timestamp

                if minutes == 0:
                    current_data = measurement
                    last_update = timestamp

                # except Exception, e:
                #     print "fail in queuefiller: %s" % e

                if len(data_queue) == settings.NO_SAMPLES:
                    break
            else:
                print measurement.location

        current_data = data_queue[0]
        current_data_at_position = current_data.rain_at_position(52, 52)

        if not current_data_at_position:

            vector = calculate_movement(data_queue, current_data.timestamp, 52)

            if vector != None:
                next_hit = extrapolate_rain(vector, data_queue[0], test_field_size)
                if next_hit:
                    print "hit in %s, size %s, intensity %s" % (next_hit['time_delta'], next_hit['size'], next_hit['intensity'])
                else:
                    print "no hit"

        return data_queue, next_hit


def build_timestamp(time, forecast=False):
    """
    Takes the given time and subtracts 8 minutes and rounds to the next lower 5minute step.
    """

    # update rate is 5min, so round to the last 5minute step
    off_minutes = time.minute % 5
    rounded_delta = timedelta(0, off_minutes*60)

    rounded_time = (time - rounded_delta).replace(second=0, microsecond=0)

    return rounded_time


def get_prediction_data(current_data, data_queue, old_data, tweet_prediction):
    # make prediction. Very much beta
    if current_data:

        next_hit = {}

        predictor = RainPredictor2(data_queue, current_data.timestamp, 18)
        try:
            time_delta, size, impact_time, hit_factor, hit_intensity = predictor.make_forecast()
            if settings.DEBUG:
                print "next rain at %s (delta %s) with size %s, hf: %s"%(impact_time, time_delta, size, hit_factor)

            if size > 0:
                next_hit['hit_factor'] = hit_factor
                # no need to be too precise
                next_hit['time_delta'] = int(time_delta)
                next_hit['size'] = int(size)
                next_hit['time'] = datetime.strftime(impact_time, "%H%M")
                next_hit['intensity'] = hit_intensity['intensity']

                if tweet_prediction:
                    from schifftszbaern.utils import send_tweet
                    try:
                        # don't send prediction if there's an old next hit value
                        if (((old_data.has_key('next_hit') and not old_data['next_hit']) or
                                 (not old_data.has_key('next_hit'))) and next_hit['time'] and hit_factor > 1.2):
                            send_tweet("t:%s, d:%s, s:%s, hf: %s, i: %s"%(next_hit['time'], next_hit['time_delta'],
                                        next_hit['size'], next_hit['hit_factor'], next_hit['intensity']))

                    except Exception, e:
                        print e
                        pass

            return next_hit

        except Exception, e:
            print e
            return {}



def build_timestamp(time, forecast=False):
    """
    Takes the given time and subtracts 8 minutes and rounds to the next lower 5minute step.
    """

    # update rate is 5min, so round to the last 5minute step
    off_minutes = time.minute % 5
    rounded_delta = timedelta(0, off_minutes * 60)

    rounded_time = (time - rounded_delta).replace(second=0, microsecond=0)

    return rounded_time

