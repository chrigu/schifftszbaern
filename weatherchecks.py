import settings

def does_it_rain(current_data):
    if current_data.location and current_data.location.has_key('intensity'):
        return True
    else:
        return False


def does_it_snow(intensity, temperature_data):
    #check for snow
    if intensity > 9:
        #if we have the current temperature doublecheck if it is cold enough
        if settings.GET_TEMPERATURE and temperature_data['status'] == 200 and float(temperature_data['temperature']) < 0.5:
            return True
        else:
            return False
    else:
        return False