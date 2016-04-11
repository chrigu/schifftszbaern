# -*- coding: utf-8 -*-
import settings
import png
import urllib
import json

from numpy import array as np_array

from scipy import ndimage
#import matplotlib.pyplot as plt
import numpy as np
import uuid
from datetime import datetime
# from utils import get_intensity


class Measurement2(object):
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

    @classmethod
    def from_json(cls, position, raster_width, test_field_width, data):
        obj = cls(position, Measurement2.timestring_to_timestamp(data['timestamp']), raster_width, test_field_width)
        obj.data = data['data']
        if 'location' in data:
            obj.location = data['location']
        else:
            obj.location = obj.rain_at_position(obj.position[0], obj.position[1])
        return obj

    @staticmethod
    def timestring_to_timestamp(timestring):
        return datetime.strptime(str(timestring), settings.DATE_FORMAT)

    # def __init__(self, position, timestamp, raster_width, test_field_width, image_data, image_name, forecast=False, url=None):
    def __init__(self, position, timestamp, raster_width, test_field_width, image_data, image_name, palette, has_alpha,
                 data, label_img, image, forecast=False, url=None):

        self.position = position
        self.raster_width = raster_width # 1px is about 850m, raster = 850m*raster_width
        self.test_field_width = test_field_width
        self.forecast = forecast
        self.location = None
        self.timestamp = timestamp
        self.image_data = image_data
        self.image_name = image_name
        self.forecast = forecast
        self.url = url
        self.palette = palette
        self.has_alpha = has_alpha
        self.data = data
        self.label_img = label_img
        self.image = image

        # self.position = position
        # self.raster_width = raster_width # 1px is about 850m, raster = 850m*raster_width
        # self.test_field_width = test_field_width
        # self.forecast = forecast
        # self.location = None
        #
        # self.has_alpha = False
        # self.palette = None
        # self.data = []
        # self.timestamp = timestamp
        # self.img_data = None
        # self.image = None
        # self.image_name = image_name
        #
        # if 'palette' in image_data[3]:
        #     self.palette = image_data[3]['palette']
        #
        # self.width = image_data[0]
        # self.height = image_data[1]
        # self.image_data = list(image_data[2])
        # self.has_alpha = image_data[3]['alpha']

    def __str__(self):
        return self.timestamp

    def __unicode__(self):
        return u"%s" % self.timestamp

    def to_json(self):

        return_dict = {
            'position': self.position,
            'queue': self.data,
            'raster_width': self.raster_width,
            'test_field_width': self.test_field_width,
            'location': self.location
        }

        return json.dumps(return_dict)

    # def analyze_image(self):
    #     pixel_array = self._read_png(self.position[0]-self.test_field_width/2, self.position[1]-self.test_field_width/2,
    #                                  self.test_field_width, self.test_field_width)
    #     if len(pixel_array) == 0:
    #         return None
    #
    #     image_data = self._make_raster(pixel_array)
    #     self.image = image_data
    #     self.data = self._analyze(image_data)
    #     self.location = self.rain_at_position(self.position[0], self.position[1])
    # #todo: rename
    # def _read_png(self, x, y, width, height):
    #     """
    #     Returns the png data starting at x, y with width & height
    #     """
    #     #todo: use ndimage
    #     pixels = []
    #     count = 0
    #
    #     for i in range(0, height):
    #         for j in range(0, width):
    #             pixels.append(self._get_color_values(x+j, y+i))
    #             count += 1
    #
    #     return pixels
    #
    # def rain_at_position(self, x, y):
    #     """
    #     Get rain intensity for position at x, y
    #     """
    #
    #     self._get_color_values(x, y)
    #     pixels = []
    #
    #     rgb_values = [0, 0, 0]
    #     for y_pos in range(y-1, y+2):
    #         for x_pos in range(x-1, x+2):
    #
    #             pixel = self._get_color_values(x, y)
    #             pixels.append(pixel)
    #
    #             for i in range(0, 3):
    #                 rgb_values[i] += pixel[i]
    #
    #     max_value = max(pixels, key=tuple)
    #     return get_intensity(np_array(max_value))
    #

    def get_data_for_label(self, label):
        for data in self.data:
            if data['label'] == label:
                return data
        return None

    # def get_color_values(self, pixel_x, pixel_y):
    #     """
    #     Returns r,g,b for a given pixel. Omits alpha data.
    #     """
    #
    #     if self.palette:
    #         pixel = self.image_data[pixel_y][pixel_x]
    #         return [self.palette[pixel][0], self.palette[pixel][1], self.palette[pixel][2]]
    #     else:
    #         if self.has_alpha:
    #             factor = 4
    #         else:
    #             factor = 3
    #
    #         if not self.has_alpha or (self.image_data[pixel_y][pixel_x * factor + 3] > 0):
    #             return [self.image_data[pixel_y][pixel_x * factor], self.image_data[pixel_y][pixel_x * factor + 1],
    #                     self.image_data[pixel_y][pixel_x * factor + 2]]
    #         else:
    #             return [0, 0, 0]

    #
    # def _make_raster(self, pixel_array):
    #     """
    #     Downsamples the image (pixel_array) so that it is =
    #      test_field_width/self.raster_width * test_field_width/self.raster_width in size.
    #     """
    #     # Divide image into a raster
    #     steps = self.test_field_width/self.raster_width
    #
    #     # create empty pixel (rgb) array
    #     raster_array = [[0, 0, 0] for i in range(steps * steps)]
    #
    #     # loop through all rasters
    #     for line in range(0, self.test_field_width):
    #         multiplicator = int(line/self.raster_width)
    #
    #         for pixel in range(0, self.test_field_width):
    #             raster = int(pixel/self.raster_width)
    #
    #             raster_no = raster+multiplicator*steps
    #
    #             for i in range(0, 3):
    #                 raster_array[raster_no][i] += pixel_array[line*self.test_field_width+pixel][i] #pixel_array[line][pixel]
    #
    #     # average pixel values
    #     for pixel in raster_array:
    #         for j in range(0, 3):
    #             pixel[j] = int(pixel[j]/(self.raster_width*self.raster_width))
    #
    #     tuple_array = []
    #
    #     # convert array to tuple
    #     for pixel in raster_array:
    #         tuple_array.append(tuple(pixel))
    #
    #     from PIL import Image
    #
    #     downsampled_image = Image.new("RGB", (steps, steps,))
    #     downsampled_image.putdata(tuple_array)
    #
    #     if settings.SAVE_IMAGES:
    #         try:
    #             downsampled_image.save('%s/%s'%(settings.RADAR_IMAGES, self.image_name))
    #         except Exception, e:
    #             print e
    #             pass
    #
    #     return downsampled_image
    #
    # def _make_mask(self, data):
    #     # make array that only indicates regions (ie raincells), so that for a given x and y 1 = rain and 0 = no rain
    #     out = []
    #
    #     for i in data:
    #         a = []
    #         for j in i:
    #             if j.any():
    #                 a.append(1)
    #             else:
    #                 a.append(0)
    #
    #         out.append(a)
    #
    #     return np.array(out)
    #
    # def _analyze(self, data):
    #     """
    #     Finds raincells and calculates center of mass & size for each cell.
    #     Returns an array with the raincells.
    #     """
    #     im = np.array(data)
    #
    #     rgb = []
    #     regions_data = self._make_mask(im)
    #
    #     # calculate position & size of the raincells (raincells are simplified (circular shape))
    #     mask = regions_data
    #     label_im, nb_labels = ndimage.label(regions_data)
    #     self.label_img = label_im
    #     # self.img_data = np.array(test)
    #     sizes = ndimage.sum(regions_data, label_im, index=range(0, nb_labels+1))
    #     mean_vals = ndimage.sum(regions_data, label_im, index=range(0, nb_labels+1))
    #     mass = ndimage.center_of_mass(mask, labels=label_im, index=range(0, nb_labels+1))
    #
    #     for n in range(0, nb_labels+1):
    #         rgb.append([0, 0, 0])
    #
    #     # calcualte color value for regions
    #     y = 0
    #     for line in label_im:
    #         x = 0
    #         for j in line:
    #             if j != 0:
    #                 for n in range(0, 3):
    #                     rgb[j.astype(int)][n] += im[y][x][n]
    #             x += 1
    #         y += 1
    #
    #     result = []
    #
    #     # calculate average color value for regions and map it to the raincell
    #     # construct array with all data FIXME: make obj instead of dict
    #     for n in range(0, nb_labels+1):
    #
    #         if sizes[n] == 0:
    #             continue
    #
    #         region = {'rgb': []}
    #         for m in range(0, 3):
    #             region['rgb'].append(rgb[n][m]/mean_vals[n])
    #
    #         # FIXME: use own class not dict
    #         # TODO: fix intensity!
    #         region['intensity'] = get_intensity(np_array([round(region['rgb'][0]), round(region['rgb'][1]),
    #                                                             round(region['rgb'][2])]))
    #
    #         region['size'] = sizes[n]
    #         region['mean_value'] = mean_vals[n]
    #         region['center_of_mass'] = [mass[n][0], mass[n][1]]
    #         region['id'] = uuid.uuid4().hex
    #         region['label'] = n
    #         # print "labels: %s"%nb_labels
    #
    #         result.append(region)
    #
    #
    #     # if one wanted a plot
    #     # plt.figure(figsize=(9,3))
    #
    #     # plt.subplot(131)
    #     # plt.imshow(label_im)
    #     # plt.axis('off')
    #     # plt.subplot(132)
    #     # plt.imshow(mask, cmap=plt.cm.gray)
    #     # plt.axis('off')
    #     # plt.subplot(133)
    #     # plt.imshow(label_im, cmap=plt.cm.spectral)
    #     # plt.axis('off')
    #
    #     # plt.subplots_adjust(wspace=0.02, hspace=0.02, top=1, bottom=0, left=0, right=1)
    #     # plt.show()
    #
    #     return result
    #
    # def _get_color_values(self, pixel_x, pixel_y):
    #     """
    #     Returns r,g,b for a given pixel. Omits alpha data.
    #     """
    #
    #     if self.palette:
    #         pixel = self.image_data[pixel_y][pixel_x]
    #         return [self.palette[pixel][0], self.palette[pixel][1], self.palette[pixel][2]]
    #     else:
    #         if self.has_alpha:
    #             factor = 4
    #         else:
    #             factor = 3
    #         if not self.has_alpha or (self.image_data[pixel_y][pixel_x*factor+3] > 0):
    #             return[self.image_data[pixel_y][pixel_x*factor], self.image_data[pixel_y][pixel_x*factor+1],
    #                    self.image_data[pixel_y][pixel_x*factor+2]]
    #         else:
    #             return [0, 0, 0]
    #
