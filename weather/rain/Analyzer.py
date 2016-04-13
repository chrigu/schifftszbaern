# -*- coding: utf-8 -*-

import settings
from Measurement import Measurement
from RainPredictor2 import RainPredictor2
from . import RadarImage
import png

from datetime import datetime, timedelta

import urllib
from . import extrapolate_rain


class Analyzer(object):

    def __init__(self, test_field_size, no_samples):

        self.test_field_size = test_field_size
        self.no_samples = no_samples

        # get date
        data_queue = []
        now = datetime.now()
        latest_radar = now - timedelta(0, 10*60)     # radar has a 8minute-ish delay, so go 10minutes back in time

        # get data from srf.ch up to now
        for minutes in range(0, self.no_samples):
            timestamp = self._build_timestamp(latest_radar - timedelta(0, 60*5*minutes))

            # try:
            # todo catch error
            # image_data, image_name = get_radar_image(timestamp=timestamp)
            # measurement = Measurement2((settings.X_LOCATION, settings.Y_LOCATION), timestamp, 1, self.test_field_size,
            #                            image_data, image_name)
            # measurement.analyze_image()
            radar_image = RadarImage((settings.X_LOCATION-52, settings.Y_LOCATION-52, settings.X_LOCATION+52, settings.Y_LOCATION+52), timestamp=timestamp)
            # measurement = Measurement2((X_LOCATION, Y_LOCATION), test_image['timestamp'], 1, 105, data, url.split("/")[:-1])
            #
            # measurement.analyze_image()
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
        rp = RainPredictor2(data_queue, current_data.timestamp, 52)
        vector = rp.calculate_movement()
        delta, data = extrapolate_rain(vector, data_queue[0], self.test_field_size)
        if data:
            print "hit in %s, size %s, intensity %s" % (delta, data['size'], data['intensity'])
        else:
            print "no hit"

    def get_timestring(self, timestamp):
        return datetime.strftime(timestamp, settings.DATE_FORMAT)

    def _build_timestamp(self, time, forecast=False):
        """
        Takes the given time and subtracts 8 minutes and rounds to the next lower 5minute step.
        """

        # update rate is 5min, so round to the last 5minute step
        off_minutes = time.minute % 5
        rounded_delta = timedelta(0, off_minutes*60)

        rounded_time = (time - rounded_delta).replace(second=0, microsecond=0)

        return rounded_time

