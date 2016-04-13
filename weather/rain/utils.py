# -*- coding: utf-8 -*-

# Created on 03/04/16
# @author: chrigu <christian.cueni@gmail.com>
from PIL import Image
import png
from scipy import ndimage
from numpy import linalg
from numpy import array as np_array
import numpy as np
import uuid
from Measurement import Measurement

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
        # png_writer.write(open("testshift%s_%s.png" % (label, index), 'wb'), img*10)

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


# def analyze_image_for_rain(position, test_field_width, timestamp, raster_width, image_data, image_name):
#
#     palette = None
#     if 'palette' in image_data[3]:
#         palette = image_data[3]['palette']
#
#     width = image_data[0]
#     height = image_data[1]
#     has_alpha = image_data[3]['alpha']
#     image_data = list(image_data[2])
#     from numpy import array
#     some = array(image_data)
#
#     pixel_array = _get_subimage(position[0] - test_field_width / 2, position[1] - test_field_width / 2,
#                                 test_field_width, test_field_width, palette, image_data, has_alpha)
#
#     if len(pixel_array) == 0:
#         return None
#
#     image = _make_raster(pixel_array, test_field_width, raster_width)
#     data, label_img = _analyze(image)
#     measurement = Measurement2(position, timestamp, raster_width, test_field_width, image_data, image_name, palette,
#                                has_alpha, data, label_img, image)
#
#     return measurement
#     # location = self.rain_at_position(self.position[0], self.position[1])

def analyze_image_for_rain(radar_image, timestamp):


    # image = _make_raster(pixel_array, test_field_width, raster_width)
    data, label_img = _analyze(radar_image._image_data)
    measurement = Measurement(radar_image, timestamp, data, label_img)

    return measurement
    # location = self.rain_at_position(self.position[0], self.position[1])


# def _get_subimage(x, y, width, height, palette, image_data, has_alpha):
#     """
#     Returns the image data starting at x, y with width & height
#     """
#     # todo: use ndimage to get
#     pixels = []
#     count = 0
#
#     for i in range(0, height):
#         for j in range(0, width):
#             pixels.append(_get_color_values(x + j, y + i, palette, image_data, has_alpha))
#             count += 1
#
#     return pixels


def _make_raster(pixel_array, test_field_width, raster_width):
    """
    Downsamples the image (pixel_array) so that it is =
     test_field_width/self.raster_width * test_field_width/self.raster_width in size.
    """
    #todo: check for ndimage methods
    # Divide image into a raster
    steps = test_field_width / raster_width

    # create empty pixel (rgb) array
    raster_array = [[0, 0, 0] for i in range(steps * steps)]

    # loop through all rasters
    for line in range(0, test_field_width):
        multiplicator = int(line / raster_width)

        for pixel in range(0, test_field_width):
            raster = int(pixel / raster_width)

            raster_no = raster + multiplicator * steps

            for i in range(0, 3):
                raster_array[raster_no][i] += pixel_array[line * test_field_width + pixel][
                    i]  # pixel_array[line][pixel]

    # average pixel values
    for pixel in raster_array:
        for j in range(0, 3):
            pixel[j] = int(pixel[j] / (raster_width * raster_width))

    tuple_array = []

    # convert array to tuple
    for pixel in raster_array:
        tuple_array.append(tuple(pixel))

    downsampled_image = Image.new("RGB", (steps, steps,))
    downsampled_image.putdata(tuple_array)

    # if settings.SAVE_IMAGES:
    #     try:
    #         downsampled_image.save('%s/%s' % (settings.RADAR_IMAGES, self.image_name))
    #     except Exception, e:
    #         print e
    #         pass

    return downsampled_image


def _analyze(data):
    """
    Finds raincells and calculates center of mass & size for each cell.
    Returns an array with the raincells.
    """
    im = np.array(data)

    rgb = []
    regions_data = _make_mask(im)

    # calculate position & size of the raincells (raincells are simplified (circular shape))
    mask = regions_data
    label_im, nb_labels = ndimage.label(regions_data)
    label_img = label_im
    # self.img_data = np.array(test)
    sizes = ndimage.sum(regions_data, label_im, index=range(0, nb_labels + 1))
    mean_vals = ndimage.sum(regions_data, label_im, index=range(0, nb_labels + 1))
    mass = ndimage.center_of_mass(mask, labels=label_im, index=range(0, nb_labels + 1))

    for n in range(0, nb_labels + 1):
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
    for n in range(0, nb_labels + 1):

        if sizes[n] == 0:
            continue

        region = {'rgb': []}
        for m in range(0, 3):
            region['rgb'].append(rgb[n][m] / mean_vals[n])

        # FIXME: use own class not dict
        # TODO: fix intensity!
        region['intensity'] = get_intensity(np_array([round(region['rgb'][0]), round(region['rgb'][1]),
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

    return result, label_img


def _make_mask(data):
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

