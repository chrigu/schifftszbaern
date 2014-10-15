import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #FIXME
from rain import Measurement, build_timestamp, RainPredictor
from datetime import datetime, timedelta
import os
import settings
import unittest

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

            measurement = Measurement((settings.X_LOCATION, settings.Y_LOCATION), test_image['timestamp'], 3, 105, \
                                        url='file:%s/testimages/%s'%(os.path.dirname(os.path.realpath(__file__)), test_image['image']))
            measurement.analyze_image()
            new_queue.append(measurement)

            if now == test_image['timestamp']:

                current_data = measurement
                old_latest_data = current_data
                latest_update = test_image['timestamp']
            

        predictor = RainPredictor(new_queue, current_data.timestamp, 18)
        try:
            delta, size, time, hit_factor = predictor.make_forecast()
            print "test: %s - time: %s (delta %s), hit_factor: %s"%(minutes_to_hit, time, delta/60, hit_factor)
        except Exception, e:
            print e
            pass
        print delta
        self.assertTrue(delta >= (minutes_to_hit-0.5)*60 and delta <= (minutes_to_hit+0.5)*60)


if __name__ == '__main__':
    unittest.main()
