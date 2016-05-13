import os, sys
from mock import patch
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #FIXME
from rain.Measurement import Measurement

from datetime import datetime, timedelta
from weatherchecks import does_it_snow
import os
import settings
from rain.RadarImage import RadarImage
from rain import extrapolate_rain
import rain.utils
from rain.utils import calculate_movement, tweet_prediction
import unittest

#Berne, Baby, Berne!
X_LOCATION = 364
Y_LOCATION = 366

#FIXME: move to tests dir
class PredictionTests(unittest.TestCase):

    def setUp(self):
        self.start_time = datetime.now()

    def test_25min(self):
        test_images = [{'timestamp': self.start_time, 'image': 'test_25min_6.png'},
                        {'timestamp': self.start_time-timedelta(0, 60*5), 'image': 'test_25min_5.png'}]
                        # {'timestamp':self.start_time-timedelta(0,60*10), 'image':'test_20min_4.png'},
                        # {'timestamp':self.start_time-timedelta(0,60*15), 'image':'test_20min_3.png'},
                        # {'timestamp':self.start_time-timedelta(0,60*20), 'image':'test_20min_2.png'},
                        # {'timestamp':self.start_time-timedelta(0,60*25), 'image':'test_20min_1.png'}]

        self._test_images(test_images, 25)

    def test_40min(self):
        test_images = [{'timestamp': self.start_time, 'image': 'test_40min_6.png'},
                       {'timestamp': self.start_time-timedelta(0, 60*5), 'image': 'test_40min_5.png'}]

        self._test_images(test_images, 40)

    # def test_43min(self):
    #
    #     test_images = [{'timestamp': self.start_time, 'image': 'test_43min_2.png'},
    #                     {'timestamp': self.start_time-timedelta(0, 60*5), 'image': 'test_43min_1.png'}]
    #
    #     self._test_images(test_images, 43)


    # def test(self):

    #     test_images = [{'timestamp':self.start_time, 'image':'test_6.png'}, \
    #                     {'timestamp':self.start_time-timedelta(0,60*5), 'image':'test_5.png'}]

    #     self._test_images(test_images, 20)
    def test_history(self):

        images1 = [{'timestamp': self.start_time - timedelta(0, 60 * 15), 'image': 'test_history_4.png'},
                   {'timestamp': self.start_time - timedelta(0, 60 * 20), 'image': 'test_history_3.png'}]

        images2 = [{'timestamp': self.start_time - timedelta(0, 60 * 10), 'image': 'test_history_5.png'},
                   {'timestamp': self.start_time - timedelta(0, 60 * 15), 'image': 'test_history_4.png'}]

        images3 = [{'timestamp': self.start_time, 'image': 'test_history_6.png'},
                   {'timestamp': self.start_time - timedelta(0, 60 * 5), 'image': 'test_history_5.png'}]

        queue1, current1, vector1, history1, oldest_hit = self._get_history(images1)
        queue2, current2, vector2, history2, old_hit = self._get_history(images2, old_hit=oldest_hit,
                                                                         old_sample=current1)

        queue3, current3 = self._get_measurement(images3, old_sample=current2)
        vector3, history3 = calculate_movement(queue3, current3.timestamp, 52)

        next_hit = extrapolate_rain(vector3, queue3[0], 105, history=history3, old_hit=old_hit)

        self.assertEqual(next_hit['ancestors'], [oldest_hit['id'], old_hit['id'], next_hit['id']])

    #todo rename
    def _get_history(self, images, old_hit=None, old_sample=None):
        queue, current = self._get_measurement(images, old_sample=old_sample)
        vector, history = calculate_movement(queue, current.timestamp, 52)
        next_hit = extrapolate_rain(vector, queue[0], 105, history=history, old_hit=old_hit)

        return queue, current, vector, history, next_hit


    def _get_measurement(self, images, old_sample=None):
        # some initialization
        new_queue = []
        current_data = None

        # get date
        now = images[0]['timestamp']

        # get old data up to now - 5*5minutes
        # note: We might not be using everything here
        i = 0
        for test_image in images:

            if not old_sample or old_sample and i == 0:

                # todo: do in fn
                url = 'file:%s/testimages/%s' % (os.path.dirname(os.path.realpath(__file__)), test_image['image'])
                radar_image = RadarImage((X_LOCATION - 52, Y_LOCATION - 52, X_LOCATION + 52, Y_LOCATION + 52), url=url)
                measurement = Measurement(radar_image, test_image['timestamp'])
                new_queue.append(measurement)

                if now == test_image['timestamp']:
                    current_data = measurement

            else:
                new_queue.append(old_sample)

            i += 1

        current_data = new_queue[0]

        return new_queue, current_data

    def _get_vector(self, images):
        # # some initialization
        # new_queue = []
        # current_data = None
        #
        # # get date
        # now = images[0]['timestamp']
        #
        # # get old data up to now - 5*5minutes
        # # note: We might not be using everything here
        # for test_image in images:
        #
        #     # todo: do in fn
        #     url = 'file:%s/testimages/%s' % (os.path.dirname(os.path.realpath(__file__)), test_image['image'])
        #     radar_image = RadarImage((X_LOCATION - 52, Y_LOCATION - 52, X_LOCATION + 52, Y_LOCATION + 52), url=url)
        #     measurement = Measurement(radar_image, test_image['timestamp'])
        #     new_queue.append(measurement)
        #
        #     if now == test_image['timestamp']:
        #         current_data = measurement
        #         old_latest_data = current_data
        #         latest_update = test_image['timestamp']

        new_queue, current_data = self._get_measurement(images)

        vector, history = calculate_movement(new_queue, current_data.timestamp, 52)
        #todo: fix .data on data obj. shouldn't be an obj
        if not vector == None:
            next_hit = extrapolate_rain(vector, new_queue[0], 105, history=history)
            print "hits %s, %s" % (next_hit['time_delta'], next_hit)
            return new_queue, vector, history, next_hit
        else:
            self.fail("no hit")

    def _test_images(self, images, minutes_to_hit):
        new_queue, vector, history, next_hit = self._get_vector(images)

        self.assertEqual(next_hit['ancestors'][0], new_queue[0].data[0]['id'])
        self.assertTrue(next_hit['time_delta'] >= (minutes_to_hit - 0.5)
                            and next_hit['time_delta'] <= (minutes_to_hit + 0.5))

class ImageAnalyzisTest(unittest.TestCase):

    def setUp(self):
        self.start_time = datetime.now()

    def test_rain_1mm(self):
        test_image = {'timestamp': self.start_time, 'image': 'test_rain_1mm.png'}

        self._test_image(test_image, 0)

    def test_rain_3mm(self):
        test_image = {'timestamp': self.start_time, 'image': 'test_rain_3mm.png'}

        self._test_image(test_image, 1)

    def test_rain_10mm(self):
        test_image = {'timestamp': self.start_time, 'image': 'test_rain_10mm.png'}

        self._test_image(test_image, 2)

    def test_rain_30mm(self):
        test_image = {'timestamp': self.start_time, 'image': 'test_rain_30mm.png'}

        self._test_image(test_image, 3)

    def test_rain_100mm(self):
        test_image = {'timestamp': self.start_time, 'image': 'test_rain_100mm.png'}

        self._test_image(test_image, 4)

    def test_rain_gt_100mm(self):
        test_image = {'timestamp': self.start_time, 'image': 'test_rain_gt_100mm.png'}

        self._test_image(test_image, 5)

    def test_snow_flakes(self):
        test_image = {'timestamp': self.start_time, 'image': 'test_snow_flakes.png'}

        self._test_image(test_image, 10)

    def test_snow_weak(self):
        test_image = {'timestamp': self.start_time, 'image': 'test_snow_weak.png'}

        self._test_image(test_image, 11)

    def test_snow_moderate(self):
        test_image = {'timestamp': self.start_time, 'image': 'test_snow_moderate.png'}

        self._test_image(test_image, 12)

    def test_snow_strong(self):
        test_image = {'timestamp': self.start_time, 'image': 'test_snow_strong.png'}

        self._test_image(test_image, 13)

    def test_snow_heavy(self):
        test_image = {'timestamp': self.start_time, 'image': 'test_snow_heavy.png'}

        self._test_image(test_image, 14)

    def test_snow_very_heavy(self):
        test_image = {'timestamp': self.start_time, 'image': 'test_snow_very_heavy.png'}

        self._test_image(test_image, 15)

    def _test_image(self, test_image, intensity):
        url = 'file:%s/testimages/%s' % (os.path.dirname(os.path.realpath(__file__)), test_image['image'])
        # radar_image = get_radar_image((X_LOCATION-52, Y_LOCATION-52, X_LOCATION+52, Y_LOCATION+52), url=url)
        radar_image = RadarImage((X_LOCATION-52, Y_LOCATION-52, X_LOCATION+52, Y_LOCATION+52), url=url)
        # measurement = Measurement2((X_LOCATION, Y_LOCATION), test_image['timestamp'], 1, 105, data, image_name)
        # measurement = analyze_image_for_rain(radar_image, self.start_time)
        measurement = Measurement(radar_image, self.start_time)

        # current_data = measurement.rain_at_position(X_LOCATION, Y_LOCATION)
        current_data = measurement.rain_at_position(52, 52)
        self.assertEqual(current_data['intensity'], intensity)

    def test_blankRadar(self):
        url = 'file:%s/testimages/%s' % (os.path.dirname(os.path.realpath(__file__)), 'blank_test.png')
        radar_image = RadarImage((X_LOCATION-52, Y_LOCATION-52, X_LOCATION+52, Y_LOCATION+52), url=url)
        # measurement = Measurement2((X_LOCATION, Y_LOCATION), self.start_time, 1, 105, data, image_name)
        # measurement = analyze_image_for_rain(radar_image, self.start_time)
        measurement = Measurement(radar_image, self.start_time)
        # measurement.analyze_image()
        self.assertEqual(measurement.location, None)


class WeatherTests(unittest.TestCase):

    def test_no_snow_intentsity(self):
        intensity = 4
        temperature_data = {'status': 200, 'temperature': '-3'}

        snow = does_it_snow(intensity, temperature_data)
        self.assertFalse(snow)

    def test_no_snow_status(self):
        intensity = 10
        temperature_data = {'status': 400, 'temperature': '-3'}

        snow = does_it_snow(intensity, temperature_data)
        self.assertFalse(snow)

    def test_no_snow_temperature(self):
        intensity = 10
        temperature_data = {'status': 200, 'temperature': '2'}

        snow = does_it_snow(intensity, temperature_data)
        self.assertFalse(snow)

    def test_snow(self):
        intensity = 10
        temperature_data = {'status': 200, 'temperature': '0'}

        snow = does_it_snow(intensity, temperature_data)
        self.assertTrue(snow)


class TwitterTest(unittest.TestCase):

    def test_prediction_tweet(self):
        with patch('rain.utils.send_tweet') as MockClass:
            MockClass.return_value = True

        next_hit = {
            "ancestors": ["6c06e737a5294a33b1d5d2915cba88ec"],
            "hit_factor": 2,
            "intensity":
                {"rgb": [0, 50, 255],
                 "name": "3mm/h",
                 "intensity": 1},
            "time_delta": 10,
            "id": "6c06e737a5294a33b1d5d2915cba88ec",
            "size": 2661
        }

        self.assertEqual(True, tweet_prediction(next_hit))


if __name__ == '__main__':
    unittest.main()
