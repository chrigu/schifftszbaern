# -*- coding: utf-8 -*-

from PIL import Image
from numpy import array
import cStringIO
import urllib
from rain.utils import get_timestring


class RadarImage(object):
    def __init__(self, crop_coords, url=None, timestamp=None, forecast=None):

        url, image_name = self._get_image_name(timestamp, forecast, url)

        image_file = cStringIO.StringIO(urllib.urlopen(url).read())
        image = Image.open(image_file)

        if image.palette:
            image = image.convert(mode='RGBA')

        self._image_data = array(image.crop(crop_coords))
        self._image_name = image_name
        # import scipy
        # scipy.misc.imsave(image_name, self._image_data)

        if self._image_data.shape[2] == 4:
            self._has_alpha = True
        else:
            self._has_alpha = False

    def get_rgb_for_position(self, position):
        return self._image_data[position[0]][position[1]][:-1]

    @staticmethod
    def _get_image_name(timestamp, forecast, url):

        if url and url.startswith('file:'):
            image_name = url.replace('file:', '')

        else:
            timestring = get_timestring(timestamp)

            if not forecast and not url:
                image_name = "PPIMERCATOR.%s.png" % (timestring)
            else:
                # this is sometimes not available from the website, so it is currently not used here
                image_name = "FCSTMERCATOR.%s.png" % (timestring)

            if not forecast and not url:
                url = "http://www.srfcdn.ch/meteo/nsradar/media/web/%s" % (image_name)

            # use local files. Mainly for testing

        return url, image_name
