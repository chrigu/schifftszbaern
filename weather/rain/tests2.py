import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #FIXME
from rain import Measurement, build_timestamp, RainPredictor, get_prediction_data
from datetime import datetime, timedelta
from weatherchecks import does_it_snow
import os
import settings
import unittest
from Analyzer import Analyzer

#Berne, Baby, Berne!
X_LOCATION = 364
Y_LOCATION = 366

#FIXME: move to tests dir
class PredictionTests(unittest.TestCase):

    def setUp(self):
        self.start_time = datetime.now()

    def test_16min(self):
        test_images = [{'timestamp':self.start_time, 'image':'test_16min_6.png'}, \
                        {'timestamp':self.start_time-timedelta(0,60*5), 'image':'test_16min_5.png'}]
                        # {'timestamp':self.start_time-timedelta(0,60*10), 'image':'test_20min_4.png'},
                        # {'timestamp':self.start_time-timedelta(0,60*15), 'image':'test_20min_3.png'},
                        # {'timestamp':self.start_time-timedelta(0,60*20), 'image':'test_20min_2.png'},
                        # {'timestamp':self.start_time-timedelta(0,60*25), 'image':'test_20min_1.png'}]

        self._test_images(test_images, 16)


    def test_40min(self):
        test_images = [{'timestamp':self.start_time, 'image':'test_40min_6.png'}, \
                        {'timestamp':self.start_time-timedelta(0,60*5), 'image':'test_40min_5.png'}]

        self._test_images(test_images, 40)


    def test_43min(self):

        test_images = [{'timestamp':self.start_time, 'image':'test_43min_2.png'}, \
                        {'timestamp':self.start_time-timedelta(0,60*5), 'image':'test_43min_1.png'}]

        self._test_images(test_images, 43)


    # def test(self):

    #     test_images = [{'timestamp':self.start_time, 'image':'test_6.png'}, \
    #                     {'timestamp':self.start_time-timedelta(0,60*5), 'image':'test_5.png'}]

    #     self._test_images(test_images, 20)


    def _test_images(self, images, minutes_to_hit):

        #some initialization
        queue_data = []
        forecast_data = []
        new_queue = []
        current_data = None
        old_latest_data = None
        forecast_now_data = None
        last_update = ''
        old_rain = False
        old_last_rain = None
        old_last_dry = None
        last_rain = None
        last_dry = None

        #get date
        now = images[0]['timestamp']

        #get old data up to now - 5*5minutes
        #note: We might not be using everything here
        for test_image in images:

            measurement = Measurement((X_LOCATION, Y_LOCATION), test_image['timestamp'], 3, 105, \
                                        url='file:%s/testimages/%s'%(os.path.dirname(os.path.realpath(__file__)), test_image['image']))
            measurement.analyze_image()
            new_queue.append(measurement)

            if now == test_image['timestamp']:

                current_data = measurement
                old_latest_data = current_data
                latest_update = test_image['timestamp']
            
        next_hit = get_prediction_data(current_data, new_queue, {}, False)
        predictor = RainPredictor(new_queue, current_data.timestamp, 18)
        try:
            delta, size, time, hit_factor, intensity = predictor.make_forecast()

            print "test: %s - time: %s (delta %s), hit_factor: %s"%(minutes_to_hit, time, delta/60, hit_factor)
        except Exception, e:
            print e
            pass

        self.assertTrue(delta >= (minutes_to_hit-0.5)*60 and delta <= (minutes_to_hit+0.5)*60)
        #as the time to the impact (delta) is calculated when predictor.make_forecast() is run, the result from
        #get_prediction_data (which calls predictor.make_forecast()) and predictor.make_forecast() will differ
        #as such we're adding some margins to the test +/- 1s
        self.assertTrue(float(next_hit['time_delta']) >= (delta-1) and float(next_hit['time_delta']) <= (delta+1))
        self.assertEqual(hit_factor, next_hit['hit_factor'])
        self.assertEqual(int(size), next_hit['size'])
        self.assertEqual(intensity['intensity'], next_hit['intensity'])
        self.assertEqual(datetime.strftime(time, "%H%M"), next_hit['time'])



class ImageAnalyzisTest(unittest.TestCase):

    def setUp(self):
        self.start_time = datetime.now()

    def test_rain_1mm(self):
        test_image = {'timestamp':self.start_time, 'image':'test_rain_1mm.png'}

        self._test_image(test_image, 0)

    def test_rain_3mm(self):
        test_image = {'timestamp':self.start_time, 'image':'test_rain_3mm.png'}

        self._test_image(test_image, 1)

    def test_rain_10mm(self):
        test_image = {'timestamp':self.start_time, 'image':'test_rain_10mm.png'}

        self._test_image(test_image, 2)

    def test_rain_30mm(self):
        test_image = {'timestamp':self.start_time, 'image':'test_rain_30mm.png'}

        self._test_image(test_image, 3)

    def test_rain_100mm(self):
        test_image = {'timestamp':self.start_time, 'image':'test_rain_100mm.png'}

        self._test_image(test_image, 4)

    def test_rain_gt_100mm(self):
        test_image = {'timestamp':self.start_time, 'image':'test_rain_gt_100mm.png'}

        self._test_image(test_image, 5)

    def test_snow_flakes(self):
        test_image = {'timestamp':self.start_time, 'image':'test_snow_flakes.png'}

        self._test_image(test_image, 10)

    def test_snow_weak(self):
        test_image = {'timestamp':self.start_time, 'image':'test_snow_weak.png'}

        self._test_image(test_image, 11)

    def test_snow_moderate(self):
        test_image = {'timestamp':self.start_time, 'image':'test_snow_moderate.png'}

        self._test_image(test_image, 12)

    def test_snow_strong(self):
        test_image = {'timestamp':self.start_time, 'image':'test_snow_strong.png'}

        self._test_image(test_image, 13)

    def test_snow_heavy(self):
        test_image = {'timestamp':self.start_time, 'image':'test_snow_heavy.png'}

        self._test_image(test_image, 14)

    def test_snow_very_heavy(self):
        test_image = {'timestamp':self.start_time, 'image':'test_snow_very_heavy.png'}

        self._test_image(test_image, 15)

    def _test_image(self, test_image, intensity):

        measurement = Measurement((X_LOCATION, Y_LOCATION), test_image['timestamp'], 3, 105, \
                                        url='file:%s/testimages/%s'%(os.path.dirname(os.path.realpath(__file__)), test_image['image']))

        current_data = measurement.rain_at_position(X_LOCATION, Y_LOCATION)
        self.assertEqual(current_data['intensity'], intensity)

    def test_blankRadar(self):
        measurement = Measurement((X_LOCATION, Y_LOCATION), self.start_time, 3, 105, \
                                        url='file:%s/testimages/%s'%(os.path.dirname(os.path.realpath(__file__)), 'blank_test.png'))

        measurement.analyze_image()
        self.assertEqual(measurement.location, {}) 


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

if __name__ == '__main__':
    unittest.main()
