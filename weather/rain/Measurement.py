# -*- coding: utf-8 -*-
import settings
import png
import urllib
import json

from numpy import linalg
from numpy import array as np_array

from scipy import ndimage
#import matplotlib.pyplot as plt
import numpy as np
import uuid
from datetime import datetime


class Measurement(object):
    """
    Contains rain information for the whole area for a given time

    PNG info:

    1px = approx. 850m

    *******

    radar values:

    < 1mm/h   0/150/255
    < 3mm/h   0/50/255
    < 10mm/h  0/0/200
    < 30mm/h  0/0/125
    < 100mm/h 255/255/0
    > 100mm/h 255/0/0

    Flocken 199/254/254
    schwach 150/255/255
    mässig 100/255/255
    stark 25/255/255
    sehr stark 0/255/255
    extrem 0/200/255


    """
    # move to consts file
    meteo_values = [{'name':'1mm/h', 'rgb': [0, 150, 255], 'intensity':0},
                        {'name': '3mm/h', 'rgb': [0, 50, 255], 'intensity':1},
                        {'name': '10mm/h', 'rgb': [0, 0, 200], 'intensity':2},
                        {'name': '30mm/h', 'rgb': [0, 0, 125], 'intensity':3},
                        {'name': '100mm/h', 'rgb': [255, 255, 0], 'intensity':4},
                        {'name': '>100mm/h', 'rgb': [255, 0, 0], 'intensity':5},
                        {'name': 'flakes', 'rgb': [200, 255, 255], 'intensity':10},
                        {'name': 'snow weak', 'rgb': [150, 255, 255], 'intensity':11},
                        {'name': 'snow moderate', 'rgb': [100, 255, 255], 'intensity':12},
                        {'name': 'snow strong', 'rgb': [25, 255, 255], 'intensity':13},
                        {'name': 'snow heavy', 'rgb': [0, 255, 255], 'intensity':14},
                        {'name': 'snow very heavy', 'rgb': [0, 200, 255], 'intensity':15},
                        {'name': 'blank', 'rgb': [9, 46, 69], 'intensity':-1}
    ]

    @classmethod
    def from_json(cls, position, raster_width, test_field_width, data):
        obj = cls(position, Measurement.timestring_to_timestamp(data['timestamp']), raster_width, test_field_width)
        obj.data = data['data']
        if data.has_key('location'):
            obj.location = data['location']
        else:
            obj.location = obj.rain_at_position(obj.position[0], obj.position[1])
        return obj

    @staticmethod
    def timestring_to_timestamp(timestring):
        return datetime.strptime(str(timestring), settings.DATE_FORMAT)

    def __init__(self, position, timestamp, raster_width, test_field_width, forecast=False, retries=3, url=None):

        self.position = position
        self.raster_width = raster_width # 1px is about 850m, raster = 850m*raster_width
        self.test_field_width = test_field_width
        self.forecast = forecast

        self.has_alpha = False
        self.palette = None
        self.data = []
        self.timestamp = timestamp

        timestring = self.get_timestring()

        if not forecast:
            image_name = "PPIMERCATOR.%s.png" % (timestring)
        else:
            # this is sometimes not available from the website, so it is currently not used here
            image_name = "FCSTMERCATOR.%s.png" % (timestring)

        self.image_name = image_name

        if not forecast and not url:
            url = "http://www.srfcdn.ch/meteo/nsradar/media/web/%s" % (self.image_name) 
        
        # use local files. Mainly for testing
        if url.startswith('file:'):
            r = png.Reader(file=open(url.replace('file:', ''), 'r'))
            self.local = True
        else:
            r = png.Reader(file=urllib.urlopen(url))
            self.local = False

        # get the png's properties
        try:
            data = r.read()

            if 'palette' in data[3]:
                self.palette = data[3]['palette']

            self.width = data[0]
            self.height = data[1]
            self.image_data = list(data[2])
            self.has_alpha = data[3]['alpha']

        except png.FormatError, e:
            print "%s - %s"%(url, e)
            self.width = -1
            self.height = -1            
            self.image_data = -1
            return None

    def __str__(self):
        return self.timestamp

    def __unicode__(self):
        return u"%s"%self.timestamp

    def get_timestring(self):
        return datetime.strftime(self.timestamp, settings.DATE_FORMAT)

    def to_json(self):

        return_dict = {
            'position': self.position,
            'queue': self.data,
            'raster_width': self.raster_width,
            'test_field_width': self.test_field_width,
            'location': self.location
        }

        return json.dumps(return_dict)

    def analyze_image(self):
        pixel_array = self._read_png(self.position[0]-self.test_field_width/2, self.position[1]-self.test_field_width/2,
                                     self.test_field_width, self.test_field_width)
        if len(pixel_array) == 0:
            return None

        image_data = self._make_raster(pixel_array)

        self.data = self._analyze(image_data)
        self.location = self.rain_at_position(self.position[0], self.position[1])

    def _read_png(self, x, y, width, height):
        """
        Returns the png data starting at x, y with width & height
        """

        pixels = []
        count = 0

        for i in range(0, height):
            for j in range(0, width):
                pixels.append(self._get_color_values(x+j, y+i))
                count += 1

        return pixels

    def rain_at_position(self, x, y):
        """
        Get rain intensity for position at x, y
        """

        self._get_color_values(x, y)
        pixels = []

        rgb_values = [0, 0, 0]
        for y_pos in range(y-1, y+2):
            for x_pos in range(x-1, x+2):

                pixel = self._get_color_values(x, y)
                pixels.append(pixel)

                for i in range(0,3):
                    rgb_values[i] += pixel[i]

        max_value = max(pixels, key=tuple)
        return self._get_intensity(np_array(max_value)) or {}

    def _make_raster(self, pixel_array):
        """
        Downsamples the image (pixel_array) so that it is =
         test_field_width/self.raster_width * test_field_width/self.raster_width in size.
        """

        # Divide image into a raster
        steps = self.test_field_width/self.raster_width

        # create empty pixel (rgb) array
        raster_array = [[0, 0, 0] for i in range(steps * steps)]

        # loop through all rasters
        for line in range(0, self.test_field_width):
            multiplicator = int(line/self.raster_width)

            for pixel in range(0, self.test_field_width):
                raster = int(pixel/self.raster_width)

                raster_no = raster+multiplicator*steps

                for i in range(0, 3):
                    raster_array[raster_no][i] += pixel_array[line*self.test_field_width+pixel][i] #pixel_array[line][pixel]
            
        # average pixel values
        for pixel in raster_array:
            for j in range(0,3):
                pixel[j] = int(pixel[j]/(self.raster_width*self.raster_width))

        tuple_array = []

        # convert array to tuple
        for pixel in raster_array:
            tuple_array.append(tuple(pixel))

        from PIL import Image

        downsampled_image = Image.new("RGB", (steps, steps,))
        downsampled_image.putdata(tuple_array)

        if settings.SAVE_IMAGES:
            try:
                downsampled_image.save('%s/%s'%(settings.RADAR_IMAGES, self.image_name))
            except:
                pass

        return downsampled_image

    def _analyze(self, data):
        """
        Finds raincells and calculates center of mass & size for each cell.
        Returns an array with the raincells.
        """

        im = np.array(data)

        out = []
        rgb = []

        # make array that only indicates regions (ie raincells), so that for a given x and y 1 = rain and 0 = no rain
        for i in im:
            a = []
            for j in i:
                if j.any():
                    a.append(1)
                else:
                    a.append(0)
            out.append(a)

        regions_data = np.array(out)

        # calculate position & size of the raincells (raincells are simplified (circular shape))
        mask = regions_data
        label_im, nb_labels = ndimage.label(regions_data)
        sizes = ndimage.sum(regions_data, label_im, range(1, nb_labels + 1))
        mean_vals = ndimage.sum(regions_data, label_im, range(1, nb_labels + 1))
        mass = ndimage.center_of_mass(mask, labels=label_im, index=range(1, nb_labels+1))

        for n in range(0, nb_labels):
            rgb.append([0, 0, 0])

        # calcualte color value for regions
        y = 0
        for line in label_im:
            x = 0
            for j in line:
                if j != 0:
                    for n in range(0, 3):
                        rgb[j.astype(int)-1][n] += im[y][x][n]
                x += 1
            y += 1

        result = []

        # calculate average color value for regions and map it to the raincell
        # construct array with all data FIXME: make obj instead of dict
        for n in range(0, nb_labels):
            region = {}
            region['rgb'] = []
            for m in range(0, 3):
                region['rgb'].append(rgb[n][m]/mean_vals[n])

            # FIXME: use own class not dict
            region['intensity'] = self._get_intensity(np_array([round(region['rgb'][0]), round(region['rgb'][1]),
                                                                round(region['rgb'][2])]))

            region['size'] = sizes[n]
            region['mean_value'] = mean_vals[n]
            region['center_of_mass'] = [mass[n][0], mass[n][1]]
            region['id'] = uuid.uuid4().hex

            result.append(region)


        # if one wanted a plot
        # plt.figure(figsize=(9,3))

        # plt.subplot(131)
        # plt.imshow(label_im)
        # plt.axis('off')
        # plt.subplot(132)
        # plt.imshow(mask, cmap=plt.cm.gray)
        # plt.axis('off')
        # plt.subplot(133)
        # plt.imshow(label_im, cmap=plt.cm.spectral)
        # plt.axis('off')

        # plt.subplots_adjust(wspace=0.02, hspace=0.02, top=1, bottom=0, left=0, right=1)
        # plt.show()

        return result

    def _get_color_values(self, pixel_x, pixel_y):
        """
        Returns r,g,b for a given pixel. Omits alpha data.
        """

        if self.palette:
            pixel = self.image_data[pixel_y][pixel_x]
            return [self.palette[pixel][0], self.palette[pixel][1], self.palette[pixel][2]]
        else:
            if self.has_alpha:
                factor = 4
            else:
                factor = 3
            if not self.has_alpha or (self.image_data[pixel_y][pixel_x*factor+3] > 0):
                return[self.image_data[pixel_y][pixel_x*factor], self.image_data[pixel_y][pixel_x*factor+1],
                        self.image_data[pixel_y][pixel_x*factor+2]]
            else:
                return [0,0,0]

    def _get_intensity(self, vector):
        """
        Finds the closest machting intensity on the rain scale.
        FIXME: Doesn't seem to work properly.....
        """

        # vector needs to have some minimal length
        if linalg.norm(vector) < 20:
            return None
        
        # calculate the distance to all intensities & find the minimal distance
        distances = map(lambda value: linalg.norm(vector-np_array((value['rgb'][0],value['rgb'][1],value['rgb'][2]))) ,self.meteo_values)
        min_distance = min(distances)
        
        # just check that the distance is reasonable
        if int(min_distance) < 200:
            intensity = self.meteo_values[distances.index(min(distances))]
            # check if blank image was shown:
            if intensity['intensity'] != -1:
                return intensity
        else:
            return None
