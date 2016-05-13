# -*- coding: utf-8 -*-
import settings

from datetime import datetime, timedelta

from utils import extrapolate_rain, build_timestamp
from datastorage import DataStorage
from Measurement import Measurement
from RadarImage import RadarImage
from RainPredictor import RainPredictor
from AmbientDataFetcher import AmbientDataFetcher
from utils import get_timestring, calculate_movement


def get_rain_info(x, y, test_field_size, no_samples):

        # get date
        data_queue = []
        now = datetime.now()
        next_hit = None
        latest_radar = now - timedelta(0, 10*60) # radar has a 8minute-ish delay, so go 10minutes back in time

        #todo move settings to main
        storage = DataStorage(settings.COLLECTOR_DATA_FILE)
        # load old data
        old_data = storage.load_data()

        # get data from srf.ch up to now
        for minutes in range(0, no_samples+2):
            timestamp = build_timestamp(latest_radar - timedelta(0, 60*5*minutes))

            # try to retrieve a measurement for the timestamp from the old data queue
            measurement = next((item for item in old_data['data_queue'] if item.timestamp == timestamp), None)

            # try:
            # todo catch error

            if not measurement:
                radar_image = RadarImage((x-52, y-52, x+52, y+52), timestamp=timestamp)
                measurement = Measurement(radar_image, timestamp)
            else:
                print "using stored data"

            data_queue.append(measurement)
            if settings.DEBUG:
                print "add sample with timestamp %s" % timestamp

            if len(data_queue) == settings.NO_SAMPLES:
                break

        current_data = data_queue[0]
        current_data_at_position = current_data.rain_at_position(52, 52)

        if not current_data_at_position:

            vector, history = calculate_movement(data_queue, current_data.timestamp, 52)

            if vector != None:
                next_hit = extrapolate_rain(vector, data_queue[0], test_field_size)
                if next_hit:
                    print "hit in %s, size %s, intensity %s" % (next_hit['time_delta'], next_hit['size'], next_hit['intensity'])
                else:
                    print "no hit"

        return data_queue, next_hit
