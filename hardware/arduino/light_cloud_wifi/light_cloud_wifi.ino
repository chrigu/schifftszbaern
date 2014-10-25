#include "SPI.h"
#include <Adafruit_NeoPixel.h>
#include <Adafruit_CC3000.h>
//#include <ccspi.h>
#include <string.h>
//#include "utility/debug.h"

#include <JsonParser.h>
using namespace ArduinoJson::Parser;

/* CC3000 */
// These are the interrupt and control pins
#define ADAFRUIT_CC3000_IRQ   3  // MUST be an interrupt pin!
// These can be any two pins
#define ADAFRUIT_CC3000_VBAT  5
#define ADAFRUIT_CC3000_CS    10
// Use hardware SPI for the remaining pins
// On an UNO, SCK = 13, MISO = 12, and MOSI = 11
Adafruit_CC3000 cc3000 = Adafruit_CC3000(ADAFRUIT_CC3000_CS, ADAFRUIT_CC3000_IRQ, ADAFRUIT_CC3000_VBAT,
                                         SPI_CLOCK_DIVIDER); // you can change this clock speed

#define WLAN_SSID       "yourssid"           // cannot be longer than 32 characters!
#define WLAN_PASS       "yourpassword"
// Security can be WLAN_SEC_UNSEC, WLAN_SEC_WEP, WLAN_SEC_WPA or WLAN_SEC_WPA2
#define WLAN_SECURITY   WLAN_SEC_WPA2

#define IDLE_TIMEOUT_MS  3000      // Amount of time to wait (in milliseconds) with no data
                                   // received before closing the connection.  If you know the server
                                   // you're accessing is quick to respond, you can reduce this value.

#define WEBSITE      "www.xn--schifftszbrn-pcb.ch"
#define WEBPAGE      "/api/chunntschoschiffe"

//Data PIN for NeoPixel
#define PIN 6

//time
#define TIME 5000

uint32_t ip;


//led values
byte ledValues[3]; //  RGB
int ledSteps[3]; //inc- or decrement value per color

// Parameter 1 = number of pixels in strip
// Parameter 2 = Arduino pin number (most are valid)
// Parameter 3 = pixel type flags, add together as needed:
//   NEO_KHZ800  800 KHz bitstream (most NeoPixel products w/WS2812 LEDs)
//   NEO_KHZ400  400 KHz (classic 'v1' (not v2) FLORA pixels, WS2811 drivers)
//   NEO_GRB     Pixels are wired for GRB bitstream (most NeoPixel products)
//   NEO_RGB     Pixels are wired for RGB bitstream (v1 FLORA pixels, not v2)
Adafruit_NeoPixel strip = Adafruit_NeoPixel(1, PIN, NEO_GRB + NEO_KHZ800);

void setup()
{
  //setup serial
  Serial.begin(115200);

  //initial values for color values and increment steps
  ledValues[0] = 0;
  ledValues[1] = 0;
  ledValues[2] = 0;

  ledSteps[0] = 0;
  ledSteps[1] = 0;
  ledSteps[2] = 0;

  delay(1000);

  strip.begin();
  strip.show();

  //show that we are alive
  strip.setPixelColor(0, Color(127, 0, 0));
  strip.show();
  delay(500);

  strip.setPixelColor(0, Color(0, 127, 0));
  strip.show();
  delay(500);

  strip.setPixelColor(0, Color(0, 0, 127));
  strip.show();
  delay(500);

  strip.setPixelColor(0, Color(0, 63, 127));
  strip.show();
  delay(500);
  strip.setPixelColor(0, Color(0, 0, 0));
  strip.show();
  
  /* Initialise the module */
  Serial.println(F("\nInitializing..."));
  if (!cc3000.begin())
  {
    Serial.println(F("Couldn't begin()! Check your wiring?"));
    while(1);
  }

  Serial.print(F("\nAttempting to connect to ")); Serial.println(WLAN_SSID);
  if (!cc3000.connectToAP(WLAN_SSID, WLAN_PASS, WLAN_SECURITY)) {
    Serial.println(F("Failed!"));
    while(1);
  }

  Serial.println(F("Connected!"));

  /* Wait for DHCP to complete */
  Serial.println(F("Request DHCP"));
  while (!cc3000.checkDHCP())
  {
    delay(100); // ToDo: Insert a DHCP timeout!
  }

  /* Display the IP address DNS, Gateway, etc. */
  while (! displayConnectionDetails()) {
    delay(1000);
  }

}


void loop()
{
  unsigned long count = 0;
  unsigned long refresh = 300000; //60*5*1000
  boolean parserFail = false;
  boolean gotData = false;
  int ledDelay;

  Serial.println(freeRam());
  String json_response = getData();
  strip.setPixelColor(0, Color(0, 0, 0));
  strip.show();
  //JSon
  //Serial.println(json_response);
  char jsonBuffer[128] = "";

  json_response.toCharArray(jsonBuffer, 128);
  Serial.println(jsonBuffer);
  JsonParser<16> parser;
  JsonObject root = parser.parse(jsonBuffer);

  if (!root.success()) {
    Serial.println(F("JsonParser.parse() failed"));
    parserFail = true;
    strip.setPixelColor(0, Color(0, 255, 0));
    strip.show();
    delay(500);
    strip.setPixelColor(0, Color(0, 0, 0));
    strip.show();
    delay(100);
    strip.setPixelColor(0, Color(0, 255, 0));
    strip.show();
    delay(500);
    strip.setPixelColor(0, Color(0, 0, 0));
    strip.show();
  }
  Serial.println("Json done");

  char* color = "b";
  long   timeDelta  = root["time_delta"];
  double hit_factor  = root["hit_factor"];

  if(timeDelta && hit_factor && hit_factor > 1.2) {

    gotData = true;
    Serial.println(timeDelta);
    Serial.println(hit_factor);

    if(color == "g") {
      ledValues[0] = 0;
      ledValues[1] = 127;
      ledValues[2] = 0;
      ledSteps[0] = 0;
      ledSteps[1] = 1;
      ledSteps[2] = 0;
      Serial.println(F("green"));
    } else if(color == "r") {
      ledValues[0] = 127;
      ledValues[1] = 0;
      ledValues[2] = 0;
      ledSteps[0] = 1;
      ledSteps[1] = 0;
      ledSteps[2] = 0;
      Serial.println(F("red"));
    } else if(color == "b") {
      ledValues[0] = 0;
      ledValues[1] = 0;
      ledValues[2] = 127;
      ledSteps[0] = 0;
      ledSteps[1] = 0;
      ledSteps[2] = 1;
      Serial.println(F("blue"));
    }

    //calculate delay for the right frequency
    if(timeDelta > 0 && timeDelta < 15*60) {
      ledDelay = TIME/2200;
    } else if(timeDelta > 25*60 && timeDelta >= 15*60) {
      ledDelay = TIME/1000;
    } else if(timeDelta >= 25*60) {
      ledDelay = TIME/400;
    }
    Serial.println(ledDelay);

    //blink led for 5 minutes
    while(count < refresh){
      for(int i = 0;i < 3;i++){
        int nextValue = ledValues[i] + ledSteps[i];
        if(nextValue > 127 || nextValue < 0){
          ledSteps[i] = -1*ledSteps[i];
        }
        ledValues[i] += ledSteps[i];
      }
      setColor(ledValues[0], ledValues[1], ledValues[2]);
      count += ledDelay;
      delay(ledDelay);
    }
  } else {
    Serial.println(F("no data"));
  }

  if(gotData){
    delay(10);
  } else {
    delay(refresh);
  }
  Serial.println(freeRam());
}

/**************************************************************************/
/*!
    @brief  set the color of all pixels
*/
/**************************************************************************/
void setColor(int red, int green, int blue)
{
  int i;
  for (i=0; i < strip.numPixels(); i++) {
      strip.setPixelColor(i, Color(green, blue, red));
  }
   strip.show();
}

/**************************************************************************/
/*!
    @brief  Create a 24 bit color value from R,G,B
*/
/**************************************************************************/
uint32_t Color(byte r, byte g, byte b)
{
  uint32_t c;
  c = b;
  c <<= 8;
  c |= r;
  c <<= 8;
  c |= g;
  return c;
}


/**************************************************************************/
/*!
    @brief  Tries to read the IP address and other connection details
*/
/**************************************************************************/
bool displayConnectionDetails(void)
{
  uint32_t ipAddress, netmask, gateway, dhcpserv, dnsserv;

  if(!cc3000.getIPAddress(&ipAddress, &netmask, &gateway, &dhcpserv, &dnsserv))
  {
    Serial.println(F("Unable to retrieve the IP Address!\r\n"));
    return false;
  }
  else
  {
    Serial.print(F("\nIP Addr: ")); cc3000.printIPdotsRev(ipAddress);
    Serial.print(F("\nNetmask: ")); cc3000.printIPdotsRev(netmask);
//    Serial.print(F("\nGateway: ")); cc3000.printIPdotsRev(gateway);
//    Serial.print(F("\nDHCPsrv: ")); cc3000.printIPdotsRev(dhcpserv);
//    Serial.print(F("\nDNSserv: ")); cc3000.printIPdotsRev(dnsserv);
//    Serial.println();
    return true;
  }
}

/**************************************************************************/
/*!
    @brief  Connects to the WLAN and retrieves the data
*/
/**************************************************************************/
String getData(void)
{

  ip = 0;
  // Try looking up the website's IP address
  Serial.print(WEBSITE); Serial.print(F(" -> "));
  while (ip == 0) {
    if (! cc3000.getHostByName(WEBSITE, &ip)) {
      Serial.println(F("Couldn't resolve!"));
    }
    delay(500);
  }

  cc3000.printIPdotsRev(ip);

   Adafruit_CC3000_Client www = cc3000.connectTCP(ip, 80);
  if (www.connected()) {
    www.fastrprint(F("GET "));
    www.fastrprint(F(WEBPAGE));
    www.fastrprint(F(" HTTP/1.1\r\n"));
    www.fastrprint(F("Host: ")); www.fastrprint(WEBSITE); www.fastrprint(F("\r\n"));
    www.fastrprint(F("\r\n"));
    www.println();
  } else {
    Serial.println(F("Connection failed"));
    //display error
    strip.setPixelColor(0, Color(255, 0, 0));
    strip.show();
    delay(500);
    strip.setPixelColor(0, Color(0, 0, 0));
    strip.show();
    delay(100);
    strip.setPixelColor(0, Color(255, 0, 0));
    strip.show();
    delay(500);
    strip.setPixelColor(0, Color(0, 0, 0));
    strip.show();
    return "";
  }


  Serial.println(F("-------------------------------------"));
  String json_response = "";

  bool begin = false;
  /* Read data until either the connection is closed, or the idle timeout is reached. */
  unsigned long lastRead = millis();
  while (www.connected() && (millis() - lastRead < IDLE_TIMEOUT_MS)) {
    while (www.available()) {
      char c = www.read();
      if (c == '{') {
          begin = true;
      }

      if (begin) {
        json_response += (c);
      }

      lastRead = millis();
    }
  }
  www.close();
  Serial.println(F("-------------------------------------"));

  /* You need to make sure to clean up after yourself or the CC3000 can freak out */
  /* the next time your try to connect ... */
  //Serial.println(F("\n\nDisconnecting"));
  //cc3000.disconnect();

  return json_response;
}

int freeRam () {
  extern int __heap_start, *__brkval; 
  int v; 
  return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval); 
}
