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
from numpy import linalg

# from utils import get_intensity

#todo move to const
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

    @classmethod
    def from_json(cls, timestamp, queue, location, label_img):
        #todo: use setters
        obj = cls(None, Measurement.timestring_to_timestamp(timestamp), data=queue, label_img=np.array(label_img))
        if location:
            obj.location = location
        #FIXME: needed below?
        # else:
        #     obj.location = obj.rain_at_position(obj.position[0], obj.position[1])
        return obj

    @staticmethod
    def timestring_to_timestamp(timestring):
        return datetime.strptime(str(timestring), settings.DATE_FORMAT)

    # def __init__(self, position, timestamp, raster_width, test_field_width, image_data, image_name,
    #       forecast=False, url=None):
    def __init__(self, radar_image, timestamp, forecast=False, url=None, data=None, label_img=None):

        self.forecast = forecast
        #todo: still used?
        self.location = None
        self.timestamp = timestamp
        self.forecast = forecast
        self.url = url
        self.radar_image = radar_image
        if data and label_img is not None:
            self.data = data
            self.label_img = label_img
        else:
            image_data = self._make_raster(self.radar_image._image_data)
            self.data, self.label_img = self._analyze(image_data)

    def __str__(self):
        return self.timestamp

    def __unicode__(self):
        return u"%s" % self.timestamp

    def to_dict(self):

        return_dict = {
            'queue': self.data,
            'location': self.location,
            'label_img': self.label_img.tolist(),
            'timestamp': datetime.strftime(self.timestamp, settings.DATE_FORMAT)
        }

        return return_dict

    def to_json(self):
        return json.dumps(self.to_dict())

    def rain_at_position(self, x, y):
        """
        Get rain intensity for position at x, y
        """

        if not self.radar_image:
            return None

        pixels = []

        rgb_values = [0, 0, 0]
        for y_pos in range(y - 1, y + 2):
            for x_pos in range(x - 1, x + 2):

                pixel = self.radar_image.get_rgb_for_position((x, y))
                pixels.append(pixel)

                for i in range(0, 3):
                    rgb_values[i] += pixel[i]

        max_value = max(pixels, key=tuple)
        return self._get_intensity(max_value) or None

    def _get_intensity(self, rgb_vector):
        """
        Finds the closest matching intensity for a given color
        """
        # rgb_vector needs to have some minimal length
        if linalg.norm(rgb_vector, ord=1) < 50:
            return None

        # calculate the distance to all intensities & find the minimal distance
        distances = map(
            lambda value: linalg.norm(rgb_vector - np_array((value['rgb'][0], value['rgb'][1], value['rgb'][2]))),
            RAIN_INTENSITIES)
        min_distance = min(distances)

        # just check that the distance is reasonable
        if int(min_distance) < 200:
            intensity = RAIN_INTENSITIES[distances.index(min(distances))]
            # check if blank image was shown:
            if intensity['intensity'] != -1:
                return intensity
        else:
            return None

    def _get_color_values(self, pixel_x, pixel_y):
        """
        Returns r,g,b for a given pixel. Omits alpha data.
        """
        print self.radar_image.get_rgb_for_position((0, 0))
        if self.radar_image._has_alpha:
            factor = 4
        else:
            factor = 3
        if not self.radar_image._has_alpha or (self.radar_image._image_data[pixel_y][pixel_x * factor + 3] > 0):
            return [self.radar_image._image_data[pixel_y][pixel_x * factor],
                    self.radar_image._image_data[pixel_y][pixel_x * factor + 1],
                    self.radar_image._image_data[pixel_y][pixel_x * factor + 2]]
        else:
            return [0, 0, 0]

    def get_data_for_label(self, label):
        for data in self.data:
            if data['label'] == label:
                return data
        return None

    def _make_raster(self, pixel_array):
        """
        Downsamples the image (pixel_array) so that it is =
         test_field_width/self.raster_width * test_field_width/self.raster_width in size.
        """
        #todo: do better

        image_array = []

        #removes alpha channel
        if len(pixel_array[0][0]) == 4:
            for row in pixel_array:
                new_row = []
                for pixel in row:
                    if pixel[3] > 127:
                        new_pixel = [pixel[0], pixel[1], pixel[2]]
                    else:
                        new_pixel = [0, 0, 0]
                    new_row.append(new_pixel)
                image_array.append(new_row)

        return image_array

    def _make_mask(self, data):
        # make array that only indicates regions (ie raincells), so that for a given x and y 1 = rain and 0 = no rain
        out = []

        for i in data:
            a = []
            for j in i:
                if j.any():
                    a.append(1)
                else:
                    a.append(0)

            out.append(a)

        return np.array(out)

    def _analyze(self, data):
        """
        Finds raincells and calculates center of mass & size for each cell.
        Returns an array with the raincells.
        """
        im = np.array(data)

        rgb = []
        regions_data = self._make_mask(im)

        # calculate position & size of the raincells (raincells are simplified (circular shape))
        mask = regions_data
        label_im, nb_labels = ndimage.label(regions_data)
        self.label_img = label_im
        # self.img_data = np.array(test)
        sizes = ndimage.sum(regions_data, label_im, index=range(0, nb_labels+1))
        mean_vals = ndimage.sum(regions_data, label_im, index=range(0, nb_labels+1))
        mass = ndimage.center_of_mass(mask, labels=label_im, index=range(0, nb_labels+1))

        for n in range(0, nb_labels+1):
            rgb.append([0, 0, 0])

        # calcualte color value for regions
        y = 0
        for line in label_im:
            x = 0
            for j in line:
                if j != 0:
                    for n in range(0, 3):
                        rgb[j.astype(int)][n] += im[y][x][n]
                x += 1
            y += 1

        result = []

        # calculate average color value for regions and map it to the raincell
        # construct array with all data FIXME: make obj instead of dict
        for n in range(0, nb_labels+1):

            if sizes[n] == 0:
                continue

            region = {'rgb': []}
            for m in range(0, 3):
                region['rgb'].append(rgb[n][m]/mean_vals[n])

            # FIXME: use own class not dict
            # TODO: fix intensity!
            region['intensity'] = self._get_intensity(np_array([round(region['rgb'][0]), round(region['rgb'][1]),
                                                                round(region['rgb'][2])]))

            region['size'] = sizes[n]
            region['mean_value'] = mean_vals[n]
            region['center_of_mass'] = [mass[n][0], mass[n][1]]
            region['id'] = uuid.uuid4().hex
            region['label'] = n
            # print "labels: %s"%nb_labels

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

        return result, label_im

