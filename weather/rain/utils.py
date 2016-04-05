# -*- coding: utf-8 -*-

# Created on 03/04/16
# @author: chrigu <christian.cueni@gmail.com>
import png
from scipy import ndimage
from numpy import linalg
from numpy import array as np_array

"""

radar values from http://www.srf.ch/meteo/radar

rain
< 1mm/h   0/150/255
< 3mm/h   0/50/255
< 10mm/h  0/0/200
< 30mm/h  0/0/125
< 100mm/h 255/255/0
> 100mm/h 255/0/0

snow
Flocken 199/254/254
schwach 150/255/255
mässig 100/255/255
stark 25/255/255
sehr stark 0/255/255
extrem 0/200/255


"""

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


def extrapolate_rain(vector, sample, test_field_size):
    print "shifting image %s %s" % (vector.tolist(), type(vector))

    png_writer = png.Writer(width=test_field_size, height=test_field_size, greyscale=True)
    for index in range(1, 15):

        value_sum = 0
        label = -1

        rounded_vector = map(lambda x: round(x * index), vector)  # todo: test
        img = ndimage.shift(sample.label_img, rounded_vector, mode='nearest')
        label = img[int(test_field_size / 2)][int(test_field_size / 2)]  # todo: test area not point
        png_writer.write(open("testshift%s_%s.png" % (label, index), 'wb'), img*10)

        for x in range((test_field_size / 2) - 2, (test_field_size / 2) + 3):
            for y in range((test_field_size / 2) - 2, (test_field_size / 2) + 3):
                value_sum += img[x][y]
                #todo assign label
                # if label == -1:
                #     label = img[test_field_size/2][test_field_size/2]

        if label > 0:
            print "hit, label %s in %s minutes" % (label, index * 10)
            return index * 5, sample.get_data_for_label(label)

    return -1, None


def get_intensity(rgb_vector):
    """
    Finds the closest matching intensity for a given color
    """

    # rgb_vector needs to have some minimal length
    if linalg.norm(rgb_vector) < 20:
        return None

    # calculate the distance to all intensities & find the minimal distance
    distances = map(lambda value: linalg.norm(rgb_vector - np_array((value['rgb'][0], value['rgb'][1], value['rgb'][2]))),
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
