import os
import server
import unittest
import tempfile
import json
from datetime import datetime, timedelta
import dateutil.parser


class ApiTestCase(unittest.TestCase):

    def setUp(self):
        #overwrite settings
        self.data_file, server.app.config['DATA_FILE'] = tempfile.mkstemp()
        server.app.config['DRY_SINCE_MESSAGE'] = 'No rain since'
        server.app.config['DRY_MESSAGE'] = 'Dry'
        server.app.config['RAIN_SINCE_MESSAGE'] = 'Rain since'
        server.app.config['RAIN_MESSAGE'] = 'Raining'
        server.app.config['SNOW_SINCE_MESSAGE'] = 'Snow since'
        server.app.config['SNOW_MESSAGE'] = 'Snowing'
        server.app.config['SECRET'] = 'secret'
        self.app = server.app.test_client()
        self.now = datetime.now()

    def tearDown(self):
        os.close(self.data_file)
        os.unlink(server.app.config['DATA_FILE'])

    def _test_main(self, last_update_string, situation_message, since_message, body_class_regex):
        
        response = self.app.get('/')

        #print response.data

        self.assertIn(situation_message, response.data)
        self.assertIn(last_update_string, response.data)
        self.assertIn(since_message, response.data)
        self.assertRegexpMatches(response.data, body_class_regex)

    def _test_api_no_login(self, url):
        current_data = {    'intensity': 10,
                            'rgb': [255, 233, 200]
                        }
        data_to_send = {'prediction':[], 'current_data':current_data, 'temperature':{'status':200, 'temperature':"10.1"}, 
                        'snow':False}

        payload = {'secret':'someother', 'data':json.dumps(data_to_send)}

        response = self.app.post(url, data=payload)        
        self.assertEquals(response.status, '401 UNAUTHORIZED')

    def test_api_rainupdate_no_login(self):

        self._test_api_no_login(server.app.config['RAIN_UPDATE_PATH'])


    # def test_api_weatherupdate_no_login(self):

    #     self._test_api_no_login(server.app.config['WEATHER_UPDATE_PATH'])


    def _test_api_update(self, payload, data, last_update_rain, snow, last_rain_intensity, temperature, weather_symbol_id):

        response = self.app.post(server.app.config['RAIN_UPDATE_PATH'], data=payload)

        #read data from file
        file_json = server.read_from_file()

        self.assertEquals(file_json['snow'], snow)
        self.assertEquals(file_json['last_update_rain'], last_update_rain)
        self.assertEquals(file_json['last_rain_intensity'], data['current_data']['intensity'])
        self.assertEquals(file_json['temperature'], temperature['temperature'])
        self.assertEquals(file_json['weather_symbol_id'], weather_symbol_id)

    def test_api_rainupdate(self):
        snow = False
        temperature = {'status':200, 'temperature':"10.1"}

        current_data = {'intensity': 9,
                        'rgb': [255, 233, 200]
                        }
        current_weather = {"coord_y": 204410, "coord_x": 601930, "weather_symbol_id": 5, "timestamp": "20150115131200", "altitude": 553, 
                          "date": "Today, 15 January 2015, 13:00", "min_zoom": 2, "weekday": "Today", "current_temp": 5.8, 
                          "city_name": "Bern / Zollikofen", "location_id": "BER", "name": "Bern / Zollikofen"
                          }
        data_to_send = {'prediction':[], 'current_data':current_data, 'temperature':temperature, 
                        'snow':snow, 'current_weather':current_weather}

        payload = {'secret':server.app.config['SECRET'], 'data':json.dumps(data_to_send)}

        self._test_api_update(payload, data_to_send, True, snow, current_data['intensity'], temperature, current_weather['weather_symbol_id'])

    def test_api_snowupdate(self):
        snow = True
        temperature = {'status':200, 'temperature':"0.1"}

        current_data = {'intensity': 12,
                        'rgb': [255, 233, 200]
                        }
        current_weather = {"coord_y": 204410, "coord_x": 601930, "weather_symbol_id": 5, "timestamp": "20150115131200", "altitude": 553, 
                          "date": "Today, 15 January 2015, 13:00", "min_zoom": 2, "weekday": "Today", "current_temp": 5.8, 
                          "city_name": "Bern / Zollikofen", "location_id": "BER", "name": "Bern / Zollikofen"
                          }
        data_to_send = {'prediction':[], 'current_data':current_data, 'temperature':temperature, 
                        'snow':snow, 'current_weather':current_weather}

        payload = {'secret':server.app.config['SECRET'], 'data':json.dumps(data_to_send)}

        self._test_api_update(payload, data_to_send, True, snow, current_data['intensity'], temperature, current_weather['weather_symbol_id'])

    def _test_api_schiffts(self, test_data):

        response = self.app.get('/api/schiffts')
        response_data = json.loads(response.data)

        self.assertEquals(test_data, response_data)


    def test_api_schiffts_rain(self):
        dry_since = self.now - timedelta(0,120)
        last_dry = self.now - timedelta(0,60)
        rain_since = self.now - timedelta(0,5)
        last_rain = rain_since
        last_rain_intensity = 9
        last_update_rain = True
        temperature = "10.0"
        snow = False

        test_data = { "last_rain": last_rain.isoformat(), 
                      "dry_since": dry_since.isoformat(), 
                      "rain_since": rain_since.isoformat(), 
                      "prediction": {}, 
                      "temperature": temperature, 
                      "last_dry": last_dry.isoformat(), 
                      "last_rain_intensity": last_rain_intensity, 
                      "last_update_rain": last_update_rain,
                      "snow": snow
        }

        #write test data file
        with open(server.app.config['DATA_FILE'], 'w') as outfile:
            json.dump(test_data, outfile)

        self._test_api_schiffts(test_data)


    def test_api_schiffts_snow(self):
        dry_since = self.now - timedelta(0,120)
        last_dry = self.now - timedelta(0,60)
        rain_since = self.now - timedelta(0,5)
        last_rain = rain_since
        last_rain_intensity = 11
        last_update_rain = True
        temperature = "10.0"
        snow = True

        test_data = { "last_rain": last_rain.isoformat(), 
                      "dry_since": dry_since.isoformat(), 
                      "rain_since": rain_since.isoformat(), 
                      "prediction": {}, 
                      "temperature": temperature, 
                      "last_dry": last_dry.isoformat(), 
                      "last_rain_intensity": last_rain_intensity, 
                      "last_update_rain": last_update_rain,
                      "snow": snow
        }

        #write test data file
        with open(server.app.config['DATA_FILE'], 'w') as outfile:
            json.dump(test_data, outfile)



    def test_api_schiffts_no_rain(self):
        rain_since = self.now - timedelta(0,120)
        last_rain = self.now - timedelta(0,60)
        dry_since = self.now - timedelta(0,5)
        last_dry = dry_since
        last_rain_intensity = 9
        last_update_rain = False
        temperature = "10.0"
        snow = False

        test_data = { "last_rain": last_rain.isoformat(), 
                      "dry_since": dry_since.isoformat(), 
                      "rain_since": rain_since.isoformat(), 
                      "prediction": {}, 
                      "temperature": temperature, 
                      "last_dry": last_dry.isoformat(), 
                      "last_rain_intensity": last_rain_intensity, 
                      "last_update_rain": last_update_rain,
                      "snow": snow
        }

        #write test data file
        with open(server.app.config['DATA_FILE'], 'w') as outfile:
            json.dump(test_data, outfile)

        self._test_api_schiffts(test_data)


    def test_main_no_rain(self):

        rain_since = self.now - timedelta(0,120)
        last_rain = self.now - timedelta(0,60)
        dry_since = self.now - timedelta(0,5)
        last_dry = dry_since
        last_rain_intensity = 9
        last_update_rain = False
        temperature = "10.0"

        test_data = { "last_rain": last_rain.isoformat(), 
                      "dry_since": dry_since.isoformat(), 
                      "rain_since": rain_since.isoformat(), 
                      "prediction": {}, 
                      "temperature": temperature, 
                      "last_dry": last_dry.isoformat(), 
                      "last_rain_intensity": last_rain_intensity, 
                      "last_update_rain": last_update_rain
        }

        #write test data file
        with open(server.app.config['DATA_FILE'], 'w') as outfile:
            json.dump(test_data, outfile)

        last_update_string = '<p data-lastupdate="%s">'%dateutil.parser.parse(last_dry.isoformat())

        self._test_main(last_update_string, server.app.config['DRY_MESSAGE'], server.app.config['DRY_SINCE_MESSAGE'], r'.*<body class=".*no-rain.*">.*')

    def test_main_rain(self):

        dry_since = self.now - timedelta(0,120)
        last_dry = self.now - timedelta(0,60)
        rain_since = self.now - timedelta(0,5)
        last_rain = rain_since
        last_rain_intensity = 9
        last_update_rain = True
        temperature = "10.0"

        test_data = { "last_rain": last_rain.isoformat(), 
                      "dry_since": dry_since.isoformat(), 
                      "rain_since": rain_since.isoformat(), 
                      "prediction": {}, 
                      "temperature": temperature, 
                      "last_dry": last_dry.isoformat(), 
                      "last_rain_intensity": last_rain_intensity, 
                      "last_update_rain": last_update_rain
        }

        #write test data file
        with open(server.app.config['DATA_FILE'], 'w') as outfile:
            json.dump(test_data, outfile)

        last_update_string = '<p data-lastupdate="%s">'%dateutil.parser.parse(last_rain.isoformat())

        self._test_main(last_update_string, server.app.config['RAIN_MESSAGE'], server.app.config['RAIN_SINCE_MESSAGE'], r'.*<body class=".*rain.*">.*')


    def test_main_snow(self):

        dry_since = self.now - timedelta(0,120)
        last_dry = self.now - timedelta(0,60)
        rain_since = self.now - timedelta(0,5)
        last_rain = rain_since
        last_rain_intensity = 9
        last_update_rain = True
        snow = True
        temperature = "10.0"

        test_data = { "last_rain": last_rain.isoformat(), 
                      "dry_since": dry_since.isoformat(), 
                      "rain_since": rain_since.isoformat(), 
                      "prediction": {}, 
                      "temperature": temperature, 
                      "last_dry": last_dry.isoformat(), 
                      "last_rain_intensity": last_rain_intensity, 
                      "last_update_rain": last_update_rain,
                      "snow": snow
        }

        #write test data file
        with open(server.app.config['DATA_FILE'], 'w') as outfile:
            json.dump(test_data, outfile)

        last_update_string = '<p data-lastupdate="%s">'%dateutil.parser.parse(last_rain.isoformat())

        self._test_main(last_update_string, server.app.config['SNOW_MESSAGE'], server.app.config['SNOW_SINCE_MESSAGE'], r'.*<body class=".*snow.*">.*')


if __name__ == '__main__':
    unittest.main()