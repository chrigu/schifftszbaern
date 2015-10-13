# -*- coding: utf-8 -*-

from lxml import html
import requests
import re
import json
import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)  #FIXME: only used for localhost
import settings

DOMAIN = "www.meteoswiss.admin.ch"
# get page
page = requests.get("http://%s/home/weather/measurement-values/current-weather.html"%DOMAIN)
tree = html.fromstring(page.text)

# get url for json
map_div = tree.xpath("//div[@id='current-weather-map']/@data-json-url")

if len(map_div) > 0:
    berne_data = {}
    data_response = requests.get('http://%s%s'%(DOMAIN, map_div[0]))
    if data_response.status_code == 200:
        print data_response.json()
        for location in data_response.json()['data']:

            if location['location_id'] == settings.SMN_CODE:
                berne_data = location

    print berne_data



# if img_tag and berne_div:
#     #find and extract the weather description
#     match_obj_weather = re.match( r'(\w+):\s+(.+)', img_tag[0])
#     weather_string = match_obj_weather.group(2)
#
#     #extract array if more than one description exists
#     if "," in weather_string:
#         weather_array = map(lambda w_string: w_sting.strip(), weather_string.split(","))
#     else:
#         weather_array = [weather_string.strip()]
#
#     #find and extract temperature
#     match_obj_temp = re.match( r'(\d+\.\d?).+', berne_div[0])
#
#     #send to server
#     if match_obj_weather and match_obj_temp:
#         payload = {'secret':settings.SECRET, 'data':json.dumps({'weather':weather_array, 'temperature':match_obj_temp.group(1)})}
#         r = requests.post(settings.SERVER_WEATHER_URL, data=payload)
