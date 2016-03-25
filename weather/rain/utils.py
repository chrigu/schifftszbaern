# -*- coding: utf-8 -*-

# Created on 03/04/16
# @author: chrigu <christian.cueni@gmail.com>
import png
from scipy import ndimage


def extrapolate_rain(vector, sample, test_field_size):
    print "shifting image %s %s" % (vector.tolist(), type(vector))

    png_writer = png.Writer(width=test_field_size, height=test_field_size, greyscale=True)
    for index in range(1, 15):

        values = 0
        label = -1

        rounded_vector = map(lambda x: round(x * index), vector)  # todo: test
        img = ndimage.shift(sample.label_img, rounded_vector, mode='nearest')
        label = img[int(test_field_size / 2)][int(test_field_size / 2)]  # todo: test area not point
        png_writer.write(open("testshift%s_%s.png" % (label, sample.image_name), 'wb'), img)

        for x in range(((test_field_size) / 2) - 2, ((test_field_size) / 2) + 3):
            for y in range(((test_field_size) / 2) - 2, ((test_field_size) / 2) + 3):
                values += img[x][y]
                if label == -1:
                    label = img[x][y]

        if label > 0:
            print "hit, label %s in %s minutes" % (label, index * 5)
            return index * 5, sample.get_data_for_label(label)

    return -1, None