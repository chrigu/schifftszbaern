//definition
var ssid = "myssid";
var passphrase = "mypassphrase";
var timeout = 5*60*1000;
var url = "http://xn--schifftszbrn-pcb.ch/api/chunntschoschiffe";

//init
var ledInterval = null;
SPI2.setup({baud:3200000, mosi:B15});
var http = require("http");
var wlan = require("CC3000").connect();
SPI2.send4bit([0,0,0], 0b0001, 0b0011);

function blinkPixel(color, frequency){
  SPI2.send4bit([255,0,0], 0b0001, 0b0011); // turn first LED Red
  var delay = Math.round(5000/frequency);
  var ledValues = [0,0,0];
  var ledSteps = [0,0,0];
  var count = 0;

  if (color == 'r') {
    ledSteps[0] = 1;
  }
  else if (color == 'g') {
    ledSteps[1] = 1;
  }
  else if (color == 'b') {
    ledSteps[2] = 1;
  }

  ledInterval = setInterval(function(){
    for(var i = 0; i < ledSteps.length; i++) {
      var nextValue = ledValues[i] + ledSteps[i];
      if(nextValue > 127 || nextValue < 0) {
          ledSteps[i] = -1*ledSteps[i];
      }
      ledValues[i] += ledSteps[i];
    }
    SPI2.send4bit(ledValues, 0b0001, 0b0011);
  }, delay);
}


function getData(){
  wlan.connect( ssid, passphrase, function (s) {
    if (s=="dhcp") {
      console.log("My IP is "+wlan.getIP().ip);
      http.get(url, function(res) {
        var contents = "";
        res.on('data', function(data) {
          contents += data;
        });
        res.on('close', function(){
          var json_data = JSON.parse(contents);
          wlan.disconnect();
          if (ledInterval !== null) {
            clearInterval(ledInterval);
          }
          if (json_data != 'undefined' && json_data.hasOwnProperty("time_delta") && json_data.prediction.hasOwnProperty("hit_factor") && json.hit_factor > 1.2) {
            console.log(json_data.prediction.time_delta);
            var frequency = 400;
            if( json_data.time_delta > 0 &&  json_data.time_delta < 15*60) {
              frequency = 2200;
            }
            else if( json_data.time_delta < 25*60 &&  json_data.time_delta >= 15*60) {
              frequency = 1000;
            }
            blinkPixel('b', frequency);
          }
          else {
            console.log('no rain');
            SPI2.send4bit([0,0,0], 0b0001, 0b0011);
          }
         });
      });
    }
  });
}

getData();
setInterval(getData, timeout);
