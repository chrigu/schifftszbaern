var ssid, password, url, timeout, apiString, ledInterval, wifiReady, http, wifi, testUrl;

//network & http stuff
ssid = "myssid";
password = "mypassword";
url = "http://www.xn--schifftszbrn-pcb.ch/api/chunntschoschiffe";
//testUrl = "http://www.xn--schifftszbrn-pcb.ch/test/chunntschoschiffe";
wifiReady = false;

//timestuff
timeout = 4.8*60*1000;

//setup
apiString = "";

function clearLed() {
    if (ledInterval) {
        clearInterval(ledInterval);
    }
    SPI2.send4bit([0, 0, 0], 0b0001, 0b0011);
}

function handleData(data) {
    var dataObj;

    clearLed();
    dataObj = JSON.parse(data);

    //empty object?
    if (Object.getOwnPropertyNames(dataObj).length !== 0) {
        if (dataObj.hasOwnProperty("time_delta") && dataObj.hasOwnProperty("hit_factor") && dataObj.hit_factor > 1.2) {
            console.log(dataObj.time_delta);
            var frequency = 400;
            if (dataObj.time_delta > 0 && dataObj.time_delta < 15 * 60) {
                frequency = 2200;
            }
            else if (dataObj.time_delta < 25 * 60 && dataObj.time_delta >= 15 * 60) {
                frequency = 1000;
            }
            blinkPixel('b', frequency);
        }
        else {
            console.log('no rain');
            SPI2.send4bit([0, 0, 0], 0b0001, 0b0011);
        }
    }
}

function blinkPixel(color, frequency) {
    var delay = Math.round(5000 / frequency);
    var ledValues = [0, 0, 0];
    var ledSteps = [0, 0, 0];

    switch (color) {
        case 'r':
            ledSteps[0] = 1;
            break;
        case 'g':
            ledSteps[1] = 1;
            break;
        case 'b':
            ledSteps[2] = 1;
            break;
    }

    //interval for blinking
    ledInterval = setInterval(function () {
        for (var i = 0; i < ledSteps.length; i++) {
            var nextValue = ledValues[i] + ledSteps[i];
            if (nextValue > 127 || nextValue < 0) {
                ledSteps[i] = -1 * ledSteps[i];
            }
            ledValues[i] += ledSteps[i];
        }
        SPI2.send4bit(ledValues, 0b0001, 0b0011);
    }, delay);
}

function getForecast() {
    if (wifiReady) {
        http.get(url, function (res) {
            apiString = "";
            res.on('data', function (data) {
                apiString += data;
                console.log(data);
            });
            res.on('close', function () {
                handleData(apiString);
            });
        });
    }
}


function onInit() {

    //funnily enough the code won't work without the timeout when you power the espruino
    //from a USB power supply. Connected to the Laptop it's ok.
    setTimeout(function() {
        http = require('http');

        digitalWrite(B9,1); // enable on Pico Shim V2

        //init serial for Wifi
        Serial2.setup(115200, {rx: A3, tx: A2});

        //init LED bus
        SPI2.setup({baud: 3200000, mosi: B15});
        SPI2.send4bit([0, 0, 0], 0b0001, 0b0011);

        wifi = require("ESP8266WiFi_0v25").connect(Serial2, function (err) {
            if (err) {
                clearLed();
            }
            console.log("Connecting to WiFi");
            wifi.connect(ssid, password, function (err) {
                if (err) {
                    clearLed();
                    throw err;
                }
                console.log("Connected");

                //add a delay just to make sure an IP address was obtained
                setTimeout(function () {
                    wifi.getIP(function (err, ip) {
                        if (err) {
                            clearLed();
                            throw err;
                        }
                        //console.log(ip);
                        wifiReady = true;
                        getForecast();
                    });
                }, 2000);
            });
        });

        setInterval(getForecast, timeout);
    }, 10000);

}