# -*- coding: utf-8 -*-
import settings
import requests
from lxml import html

from datetime import datetime


class AmbientDataFetcher(object):
    """
    fetches weather data from http://data.netcetera.com/smn/smn/<code>
    """
    @staticmethod
    def get_temperature(location_code):
        request = requests.get('http://data.netcetera.com/smn/smn/%s'%location_code)
        if request.status_code == 200:
            return 200, request.json()['temperature']
        else:
            return request.status_code, 0

    """
    Fetches the current weather from smn
    """
    @staticmethod
    def get_weather(location_code):
        DOMAIN = "www.meteoswiss.admin.ch"
        # get page
        page = requests.get("http://%s/home/weather/measurement-values/current-weather.html" % DOMAIN)
        tree = html.fromstring(page.text)

        # get url for json
        map_div = tree.xpath("//div[@id='current-weather-map']/@data-json-url")

        # get json for location
        if len(map_div) > 0:
            location_weather_data = {}
            data_response = requests.get('http://%s%s'%(DOMAIN, map_div[0]))
            if data_response.status_code == 200:
                for location in data_response.json()['data']:

                    if location['location_id'] == location_code:
                        location_weather_data = location

                location_weather_data['timestamp'] = datetime.strftime(datetime.now(), settings.DATE_FORMAT)
                return location_weather_data

        return {}