# -*- coding: utf-8 -*-

import settings


from numpy import linalg
from numpy import array as np_array

from scipy.optimize import fmin
from datetime import datetime, timedelta
import math


class RainPredictor(object):
    """
    Calculates the future movment of rain. Kind of.
    Pretty beta
    """

    def __init__(self, data, last_timestamp, center):

        # sort data by time
        self.data = sorted(data, key=lambda x: x.timestamp, reverse=True)
        self.last_timestamp = last_timestamp
        self.center = center

    def make_forecast(self):

        new_data = []
        n_1_values = []

        # add the cells from the latest samples to an arrary
        for latest_samples in self.data[0].data:
            latest_samples['forecast'] = self.data[0].forecast
            latest_samples['timestamp'] = self.data[0].timestamp
            new_data.append([latest_samples])
            n_1_values.append(latest_samples)


        # go through the rest of the data (time descending)
        for i in range(1, len(self.data)):
            # check if the samples have max. a 10min difference between them.
            try:
                dt = self.data[i-1].timestamp - self.data[i].timestamp

                if(dt.seconds > 10*60):
                    break

            except Exception, e:
                print "error: %s"%e
                continue

            close_points = {}

            # loop through all raincells for a given time and try to find the closest raincell from 5 or 10 minutes ago
            # so we can track the movement of a cell
            for sample in self.data[i].data:
                position = np_array(sample['center_of_mass'])

                # get distances to all raincells from 5 or 10 minutes ago
                distances = map(lambda new_sample: linalg.norm(position-np_array(new_sample['center_of_mass'])), n_1_values)

                if distances != []:
                    if min(distances) < 4: # just some treshold (about 9.6km (if delta is 5 minutes this is about 115km/h))
                        closest_match = n_1_values[distances.index(min(distances))]
                        if not close_points.has_key(closest_match['id']):
                            close_points[closest_match['id']] = [sample]
                        else:
                            close_points[closest_match['id']].append(sample)
                    else:
                        closest_match = None
                else:
                    closest_match = None

            # find the closest match among the cells for a given time
            for last_sample in n_1_values: # FIXME: rename to new_smample
                position = np_array(last_sample['center_of_mass'])
                if close_points.has_key(last_sample['id']):
                    distances = map(lambda close_sample: linalg.norm(position-np_array(close_sample['center_of_mass'])), close_points[last_sample['id']])
                    closest_match = close_points[last_sample['id']][distances.index(min(distances))]
                    closest_match['movement'] = position - np_array(closest_match['center_of_mass']) # FIXME: add movement to n-1 value
                    closest_match['forecast'] = self.data[i].forecast
                    closest_match['timestamp'] = self.data[i].timestamp
                else:
                    # FIXME: change to last pos
                    closest_match = {'center_of_mass':[-99, -99], 'movement':[0,0], 'size':0}
                    closest_match['forecast'] = self.data[i].forecast
                    closest_match['timestamp'] = self.data[i].timestamp

                for history in new_data:
                    if last_sample in history:
                        history.append(closest_match)

            n_1_values = self.data[i].data

        hits = []

        # Loop through a raincells history (past positions) and calculate the movement for the next 50min
        for history in new_data:

            if settings.DEBUG:
                print "***** cell forecast *****"

            # get average movement
            coms = np_array(map(lambda sample: sample['movement'], history[1:settings.NO_SAMPLES])) #FIXME: movement in wrong sample
            mean = coms.mean(axis=0)

            # get last position
            initial_position = np_array(history[0]['center_of_mass'])
            try:
                radius_abs = math.sqrt(history[0]['size']/math.pi)

            except Exception, e:
                print e
                radius_abs = 0

            if settings.DEBUG:
                print "last_pos: %s, mean %s"%(initial_position, mean)

            hit = self._find_future_hit(history[0], initial_position, radius_abs, mean, 0.5)

            if hit:
                hits.append(hit)

        next_hit_intensity = None
        time_to_next_hit = None
        next_impact_time = None
        next_size = -1
        hit_factor = 0

        if hits and settings.DEBUG:
            print "****** impacts *******"

        # loop through all cells that'll hit the location and get the one that'll hit the location the soonest
        # !FIXME: make function that gets the min value for dtime and the max value for size
        for hit in hits:
            #for sample in hit['history']:
            sample = hit['sample']
            if sample['forecast'] and sample['size'] != 0:
                last_intensity = sample['intensity']
                if(time_to_next_hit is None or time_to_next_hit > hit['dtime']):
                    if settings.DEBUG:
                        print sample
                    time_to_next_hit = hit['dtime']
                    next_impact_time = hit['timestamp']
                    next_hit_intensity = last_intensity
                    next_size = sample['size']
                    hit_factor = hit['hit_factor']
                elif time_to_next_hit == hit['dtime'] and sample['intensity'] > time_to_next_hit:
                    time_to_next_hit = hit['dtime']
                    next_hit_intensity = last_intensity
                    next_impact_time = hit['timestamp']
                    next_size = sample['size']
                    hit_factor = hit['hit_factor']

        return time_to_next_hit, next_size, next_impact_time, hit_factor, next_hit_intensity

    def _find_min_center_distance(self, initial_position, mean_movement, radius_abs):
        """
        calculate min distance of cell center to location if it keeps moving like in the past 5minutes
        """
        try:
            distance_to_location = lambda x: linalg.norm((self.center, self.center) - (x*mean_movement + initial_position))
            x_start = 0 # start from x = 0
            min_x = fmin(distance_to_location,x_start, disp=0)
            min_distance_to_location = distance_to_location(min_x)
            if min_distance_to_location != 0:
                hit_factor = radius_abs/min_distance_to_location
            else:
                hit_factor = 1000

        except Exception, e:
            min_distance_to_location = -1
            hit_factor = 0

        return hit_factor, min_distance_to_location

    def _find_future_hit(self, initial_sample, initial_position, radius_abs, mean_movement, tolerance):
            """
            calcualte minimum distance of the cell's border to the location if it keesp moving at the same speed as in
            the past 5 minutes. If it's < 0.5 the cell hits the location.
            """

            hit_factor, min_distance_to_location = self._find_min_center_distance(initial_position, mean_movement, radius_abs)

            try:
                last_time = initial_sample['timestamp']
                if initial_sample['size'] > 3:
                    radius_distance_to_location = lambda x: math.fabs(linalg.norm((self.center, self.center) -
                                                    (x*mean_movement + initial_position)) - (radius_abs+tolerance))
                    x_start = 0
                    min_x = fmin(radius_distance_to_location,x_start, disp=0)[0]
                    min_radius_distance_to_location = radius_distance_to_location(min_x)
                    forecast_sample = {}
                    forecast_sample['forecast'] = True
                    forecast_sample['center_of_mass'] = (min_x*mean_movement + initial_position)
                    forecast_sample['intensity'] = initial_sample['intensity']
                    forecast_sample['size'] = initial_sample['size']
                    time = last_time + timedelta(0,60*5*min_x)
                    forecast_sample['timestamp'] = time
                    # history.append(forecast_sample)
                    if settings.DEBUG:
                        print "%s %s - dist: %s - forecast: %s"%(forecast_sample['center_of_mass'], forecast_sample['size'], min_x, forecast_sample['forecast'])

                    # make sure the minimum value is really a hit a (somewhere from 0 to 60min in the future and within a certain
                    # distance to the location)
                    if (0 < min_x < 12) and (min_radius_distance_to_location < tolerance):
                        print forecast_sample['timestamp']
                        print (forecast_sample['timestamp']-datetime.now()).total_seconds()
                        if settings.DEBUG:
                            print "direct hit"
                            print "last: %s, timestamp: %s, now: %s"%(self.last_timestamp, forecast_sample['timestamp']-self.last_timestamp, (self.last_timestamp-datetime.now()).total_seconds())

                        return {'dtime':(forecast_sample['timestamp']-datetime.now()).total_seconds(), 'timestamp':forecast_sample['timestamp'], \
                                    'sample':forecast_sample, 'min_distance_cell_location':min_distance_to_location, 'hit_factor':hit_factor}

            except Exception, e:
                return None
