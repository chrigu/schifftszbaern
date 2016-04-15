# -*- coding: utf-8 -*-

import settings

def does_it_rain(current_data):
    '''
    check for rain, True if intensity is in dict
    '''
    if current_data and 'intensity' in current_data:
        return True
    else:
        return False


def does_it_snow(intensity, temperature_data):
    '''
    check for snow, intensity must be greater than 9 and the temperature must be below 0.5°C
    '''
    if intensity > 9:
        #if we have the current temperature doublecheck if it is cold enough
        if settings.GET_TEMPERATURE and temperature_data['status'] == 200 and float(temperature_data['temperature']) < 1.0:
            return True
        else:
            return False
    else:
        return False

