# -*- coding: utf-8 -*-

# Created on 03/04/16
# @author: chrigu <christian.cueni@gmail.com>
import os, sys
import png
from scipy import ndimage
from numpy import linalg
from numpy import array as np_array
import uuid
import math
#todo: remove
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #FIXME
import settings
from datetime import datetime, timedelta
from collections import Counter
import settings as settings
from RainPredictor import RainPredictor
import twitter
import random
import settings
import requests
import json

"""

radar values from http://www.srf.ch/meteo/radar

rain
< 1mm/h   0/150/255
< 3mm/h   0/50/255
< 10mm/h  0/0/200
< 30mm/h  0/0/125
< 100mm/h 255/255/0
> 100mm/h 255/0/0

snow
Flocken 199/254/254
schwach 150/255/255
mässig 100/255/255
stark 25/255/255
sehr stark 0/255/255
extrem 0/200/255


"""

RAIN_INTENSITIES = [{'name': '1mm/h', 'rgb': [0, 150, 255], 'intensity': 0},
                    {'name': '3mm/h', 'rgb': [0, 50, 255], 'intensity': 1},
                    {'name': '10mm/h', 'rgb': [0, 0, 200], 'intensity': 2},
                    {'name': '30mm/h', 'rgb': [0, 0, 125], 'intensity': 3},
                    {'name': '100mm/h', 'rgb': [255, 255, 0], 'intensity': 4},
                    {'name': '>100mm/h', 'rgb': [255, 0, 0], 'intensity': 5},
                    {'name': 'flakes', 'rgb': [200, 255, 255], 'intensity': 10},
                    {'name': 'snow weak', 'rgb': [150, 255, 255], 'intensity': 11},
                    {'name': 'snow moderate', 'rgb': [100, 255, 255], 'intensity': 12},
                    {'name': 'snow strong', 'rgb': [25, 255, 255], 'intensity': 13},
                    {'name': 'snow heavy', 'rgb': [0, 255, 255], 'intensity': 14},
                    {'name': 'snow very heavy', 'rgb': [0, 200, 255], 'intensity': 15},
                    {'name': 'blank', 'rgb': [9, 46, 69], 'intensity': -1}]


def tweet_status(rain, snow):
    """
    Tweets about rain/snow
    """
    # api = twitter_api()

    # print api.VerifyCredentials()

    api = twitter.Api(consumer_key=settings.CONSUMER_KEY,
                consumer_secret=settings.CONSUMER_SECRET,
                access_token_key=settings.ACCESS_TOKEN,
                access_token_secret=settings.ACCESS_TOKEN_SECRET)

    tried = []
    #twitter doesn't allow posting the same message twice so we'll just 5x with different messages
    #FIXME: save message to JSON
    for i in range(0, 5):
        try:
            if rain:
                if snow:
                    message = random.choice(settings.SNOW_MESSAGES)
                else:
                    message = random.choice(settings.RAIN_MESSAGES)
            else:
                if snow:
                    message = random.choice(settings.NO_SNOW_MESSAGES)
                else:
                    message = random.choice(settings.NO_RAIN_MESSAGES)

            if message in tried:
              continue

            send_tweet(message, api=api)
            break

        except Exception, e:
            print e
            tried.append(message)
            pass


def tweet_prediction(next_hit):
    api = twitter.Api(consumer_key=settings.PREDICTION_CONSUMER_KEY,
                      consumer_secret=settings.PREDICTION_CONSUMER_SECRET,
                      access_token_key=settings.PREDICTION_ACCESS_TOKEN,
                      access_token_secret=settings.PREDICTION_ACCESS_TOKEN_SECRET)

    send_tweet("delta:%s, s:%s, i: %s" % (next_hit['time_delta'], next_hit['size'], next_hit['intensity']['intensity']),
               api=api)

    return True


def send_tweet(message, api=None):
    return api.PostUpdate(message)


def lametric_status(rain, snow):

    # TODO: refactor, maybe do something pluginish
    if rain:
        if snow:
            message = random.choice(settings.SNOW_MESSAGES)
            icon = "a171"
        else:
            message = random.choice(settings.RAIN_MESSAGES)
            icon = "a72"
    else:
        if snow:
            message = random.choice(settings.NO_SNOW_MESSAGES)
        else:
            message = random.choice(settings.NO_RAIN_MESSAGES)

        icon = "i50"

    return send_lametric(message, icon)


def send_lametric(message, icon):
    headers = {
        "Accept": "application/json",
        "X-Access-Token": settings.LAMETRIC_TOKEN,
        "Cache-Control": "no-cache"
    }

    data = {
        "frames": [
            {
                "index": 0,
                "text": message,
                "icon": icon
             }
        ]
    }

    return requests.post(settings.LAMETRIC_URL, headers=headers, data=json.dumps(data))


def get_timestring(timestamp):
    return datetime.strftime(timestamp, settings.DATE_FORMAT)


def extrapolate_rain(vector, sample, test_field_size, old_hit=None, history=None):
    print "shifting image %s %s" % (vector.tolist(), type(vector))

    next_hit = None

    for index in range(1, 15):

        label_count = 0
        labels = []
        label = -1
        new_ancestor = None

        rounded_vector = map(lambda x: round(x * index), vector)  # todo: test
        img = ndimage.shift(sample.label_img, rounded_vector, mode='nearest')
        label = img[int(test_field_size / 2)][int(test_field_size / 2)]  # todo: test area not point
        png_writer = png.Writer(width=104, height=104, greyscale=True)
        png_writer.write(open("testshift%s_%s.png" % (label, index), 'wb'), img*5)

        for x in range((test_field_size / 2) - 1, (test_field_size / 2) + 2):
            for y in range((test_field_size / 2) - 1, (test_field_size / 2) + 2):
                if img[x][y] != 0:
                    label_count += 1
                    labels.append(img[x][y])

        print "%s, %s, %s" % (label_count, index*5, map(lambda x: x * index, vector))

        if label_count > 5:
            label = Counter(labels).keys()[0]

            data = sample.get_data_for_label(label)
            next_hit = {}
            next_hit['hit_factor'] = 2
            # no need to be too precise
            next_hit['time_delta'] = int(index * 5)
            next_hit['size'] = int(data['size'])
            next_hit['id'] = data['id']
            next_hit['intensity'] = data['intensity']
            if history and old_hit:

                # oh my.....
                for cells in history:
                    found_cells = False
                    for cell in cells:
                        if cell['id'] == data['id']:
                            found_cells = True
                        if found_cells:
                            try:
                                old_hit['ancestors'].index(cell['id'])
                                new_ancestor = cells[0]
                                break
                            except ValueError:
                                pass

                print new_ancestor

            if new_ancestor:
                next_hit['ancestors'] = old_hit['ancestors']
                next_hit['ancestors'].append(data['id'])
            else:
                next_hit['ancestors'] = [data['id']]
            print "hit, label %s in %s minutes" % (label, index * 5)
            break

    return next_hit


def _init_samples(data):
    new_data = []
    n_1_values = []

    # add the cells from the latest samples to an array
    for latest_samples in data[0].data:
        new_data.append([latest_samples])
        n_1_values.append(latest_samples)

    return new_data, n_1_values


def _find_closest_old_cells(data, newer_data):
    close_points = {}

    # loop through all raincells for a given time and try to find the closest raincell from 5 or 10 minutes ago
    # so we can track the movement of a cell
    for sample in data.data:
        position = np_array(sample['center_of_mass'])

        # get distances to all raincells from 5 or 10 minutes ago
        distances = map(lambda new_sample: linalg.norm(position - np_array(new_sample['center_of_mass'])), newer_data)

        if distances != []:

            min_distance = min(distances)
            # just some treshold (about 9.6km (if delta is 5 minutes this is about 115km/h))
            if min_distance < 4:
                closest_match = newer_data[distances.index(min_distance)]
                if not closest_match['id'] in close_points:
                    close_points[closest_match['id']] = [sample]
                else:
                    close_points[closest_match['id']].append(sample)

    return close_points


def _add_to_closest_match_to_history(data, newer_values, close_points, new_data):
    # find the closest match among the cells for a given time
    for last_sample in newer_values:  # FIXME: rename to new_smample
        position = np_array(last_sample['center_of_mass'])
        if last_sample['id'] in close_points:
            distances = map(lambda close_sample: linalg.norm(position - np_array(close_sample['center_of_mass'])),
                            close_points[last_sample['id']])
            closest_match = close_points[last_sample['id']][distances.index(min(distances))]
            closest_match['movement'] = position - np_array(
                closest_match['center_of_mass'])  # FIXME: add movement to n-1 value
            closest_match['forecast'] = data.forecast
            #FIXME: this needed below?
            # closest_match['timestamp'] = data.timestamp
        else:
            # FIXME: change to last pos
            closest_match = {
                'center_of_mass': [-99, -99],
                'movement': [0, 0],
                'size': 0
            }
            closest_match['forecast'] = data.forecast
            # closest_match['timestamp'] = data.timestamp

        for history in new_data:
            if last_sample in history:
                history.append(closest_match)

    return new_data


def _caclulate_vector(data):

    vectors = []

    for history in data:

        if settings.DEBUG:
            print "***** cell forecast *****"

        # get average movement
        coms = np_array(
            map(lambda sample: sample['movement'], history[1:settings.NO_SAMPLES]))  # FIXME: movement in wrong sample
        mean = coms.mean(axis=0)
        vectors.append(mean)

        # get last position
        initial_position = np_array(history[0]['center_of_mass'])
        try:
            radius_abs = math.sqrt(history[0]['size'] / math.pi)

        except Exception, e:
            print e

        if settings.DEBUG:
            # print "last_pos: %s, mean %s" % (initial_position, mean)
            pass

    abs_values = map(lambda vector: linalg.norm(vector, ord=1), vectors)
    if len(abs_values) > 0:
        index = abs_values.index(max(abs_values))
        return vectors[index]
    else:
        return None

def calculate_movement(data, last_timestamp, center):

    data = sorted(data, key=lambda x: x.timestamp, reverse=True)
    history = None

    new_data, n_1_values = _init_samples(data)

    # go through the rest of the data (time descending)
    for index in range(1, len(data)):
        # check if the samples have max. a 10min difference between them.
        try:
            dt = data[index - 1].timestamp - data[index].timestamp

            if dt.seconds > 10 * 60:
                break

        except Exception, e:
            print "error: %s" % e
            continue

        close_points = _find_closest_old_cells(data[index], n_1_values)
        history = _add_to_closest_match_to_history(data[index], n_1_values, close_points, new_data)

        n_1_values = data[index].data

    # todo: fix parameters
    return _caclulate_vector(new_data), history


def build_timestamp(time, forecast=False):
    """
    Takes the given time and subtracts 8 minutes and rounds to the next lower 5minute step.
    """

    # update rate is 5min, so round to the last 5minute step
    off_minutes = time.minute % 5
    rounded_delta = timedelta(0, off_minutes*60)

    rounded_time = (time - rounded_delta).replace(second=0, microsecond=0)

    return rounded_time


# def get_prediction_data(current_data, data_queue, old_data, tweet_prediction):
#     # make prediction. Very much beta
#     if current_data:
#
#         next_hit = {}
#
#         predictor = RainPredictor(data_queue, current_data.timestamp, 18)
#         try:
#             time_delta, size, impact_time, hit_factor, hit_intensity = predictor.make_forecast()
#             if settings.DEBUG:
#                 print "next rain at %s (delta %s) with size %s, hf: %s"%(impact_time, time_delta, size, hit_factor)
#
#             if size > 0:
#                 next_hit['hit_factor'] = hit_factor
#                 # no need to be too precise
#                 next_hit['time_delta'] = int(time_delta)
#                 next_hit['size'] = int(size)
#                 next_hit['time'] = datetime.strftime(impact_time, "%H%M")
#                 next_hit['intensity'] = hit_intensity['intensity']
#
#                 if tweet_prediction:
#                     from schifftszbaern.utils import send_tweet
#                     try:
#                         # don't send prediction if there's an old next hit value
#                         if (('next_hit' in old_data and not old_data['next_hit']) or
#                                  (not old_data.has_key('next_hit'))) and next_hit['time'] and hit_factor > 1.2):
#                             send_tweet("t:%s, d:%s, s:%s, hf: %s, i: %s"%(next_hit['time'], next_hit['time_delta'],
#                                         next_hit['size'], next_hit['hit_factor'], next_hit['intensity']))
#
#                     except Exception, e:
#                         print e
#                         pass
#
#             return next_hit
#
#         except Exception, e:
#             print e
#             return {}


def build_timestamp(time, forecast=False):
    """
    Takes the given time and subtracts 8 minutes and rounds to the next lower 5minute step.
    """

    # update rate is 5min, so round to the last 5minute step
    off_minutes = time.minute % 5
    rounded_delta = timedelta(0, off_minutes * 60)

    rounded_time = (time - rounded_delta).replace(second=0, microsecond=0)

    return rounded_time
