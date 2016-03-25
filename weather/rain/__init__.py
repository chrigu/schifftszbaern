# -*- coding: utf-8 -*-
import settings

from datetime import datetime, timedelta

from Measurement import Measurement
from RainPredictor import RainPredictor
from AmbientDataFetcher import AmbientDataFetcher


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

        predictor = RainPredictor(data_queue, current_data.timestamp, 18)
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




