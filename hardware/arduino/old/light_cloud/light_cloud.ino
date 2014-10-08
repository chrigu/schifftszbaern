#include "SPI.h"
#include <Adafruit_NeoPixel.h>
#include "nRF24L01.h"
#include "RF24.h"

RF24 radio(9,10);

#define PIN 6

const uint64_t pipes[1] = { 0xF0F0F0F0D1LL };

byte inData[4]; // Allocate some space for the string
char charData[4];
char inChars[3]; // Where to store the character read
byte index = 0; // Index into array; where to store the character

int led_delay = 2500/550;
byte red = 0;
byte green = 0;
byte blue = 0;

byte red_step = 1;
byte green_step = 1;
byte blue_step = 0;

boolean up = false;
boolean active = false;

// Parameter 1 = number of pixels in strip
// Parameter 2 = Arduino pin number (most are valid)
// Parameter 3 = pixel type flags, add together as needed:
//   NEO_KHZ800  800 KHz bitstream (most NeoPixel products w/WS2812 LEDs)
//   NEO_KHZ400  400 KHz (classic 'v1' (not v2) FLORA pixels, WS2811 drivers)
//   NEO_GRB     Pixels are wired for GRB bitstream (most NeoPixel products)
//   NEO_RGB     Pixels are wired for RGB bitstream (v1 FLORA pixels, not v2)
Adafruit_NeoPixel strip = Adafruit_NeoPixel(1, PIN, NEO_GRB + NEO_KHZ800);
 
String serialCommand = "";         // a string to hold incoming data
boolean stringComplete = false;

void setup()
{
  Serial.begin(57600);
  radio.begin();
  
  radio.setDataRate(RF24_1MBPS);
  radio.setPALevel(RF24_PA_MAX);
  radio.setChannel(76);
  radio.enableDynamicPayloads();
  radio.setRetries(15,15);
  
  radio.setCRCLength(RF24_CRC_16);
  radio.openReadingPipe(0,pipes[0]);

  radio.startListening();
  radio.printDetails();
  
  delay(1000);
  
  strip.begin();
  strip.show();
  
  inData[0] = 255;
  inData[1] = 255;
  inData[2] = 0;
  
  //show that we are alive
  strip.setPixelColor(0, Color(255, 0, 0));
  strip.show();
  delay(1000);
   
  strip.setPixelColor(0, Color(0, 255, 0));
  strip.show();
  delay(1000);
   
  strip.setPixelColor(0, Color(0, 0, 255));
  strip.show();
  delay(1000);
   
  strip.setPixelColor(0, Color(0, 125, 125));
  strip.show();
  delay(1000);
  strip.setPixelColor(0, Color(0, 0, 0));
  strip.show();
}
 
void loop()
{
    char receivePayload[63];
    uint8_t len = 0;
    uint8_t pipe = 0;
           
    // Loop thru the pipes 0 to 5 and check for payloads
    if ( radio.available(&pipe) ) {
      
      bool done = false;
      while (!done)
      {
        len = radio.getDynamicPayloadSize();  
        done = radio.read( &receivePayload,len );
        
        // Format string for printing ending with 0
        receivePayload[len] = 0;
        //Serial.println(printf("Got payload: %s len:%s",receivePayload,len));
        }        
        serialCommand = receivePayload;
        stringComplete = true;
        Serial.println("done");
        //radio.startListening();
      
      }
  //read command
  if (stringComplete) {

    Serial.println(serialCommand);
    String color;
    String delay_string;
    int separator = serialCommand.indexOf(":");
    if(separator != -1){
      color = serialCommand.substring(0,separator);
      delay_string = serialCommand.substring(separator+1, serialCommand.length());
      char valueArray[delay_string.length() + 1];
      delay_string.toCharArray(valueArray, sizeof(valueArray));
      Serial.println(valueArray);
      led_delay = 2500/atoi(valueArray);
      Serial.println(led_delay);
    }
    if(color == "g") {
      active = true;
      inData[0] = 0;
      inData[1] = 255;
      inData[2] = 0;
      red_step = 0;
      green_step = 1;
      blue_step = 0;
      Serial.println("green"); 
    } else if(color == "r") {
      active = true;
      inData[0] = 255;
      inData[1] = 0;
      inData[2] = 0;
      red_step = 1;
      green_step = 0;
      blue_step = 0; 
      Serial.println("red"); 
    } else if(color == "b") {
      active = true;
      inData[0] = 0;
      inData[1] = 0;
      inData[2] = 0;
      red_step = 0;
      green_step = 0;
      blue_step = 1; 
      Serial.println("blue"); 
     } else if(color == "q") {
      active = false; 
      strip.setPixelColor(0, Color(0, 0, 0));
      strip.show();
      Serial.println("inactive"); 
    }
         
    up = false;
    serialCommand = "";
    stringComplete = false;
  }  
  
  if(up) {
    if(red_step == 1) {
      inData[0]++;
    }
    if(green_step == 1){
      inData[1]++;
    }
     if(blue_step == 1){
      inData[2]++;
    }  
  }
  else {
    if(red_step == 1) {
      inData[0]--;
    }
    if(green_step == 1){
      inData[1]--;
    }
     if(blue_step == 1){
      inData[2]--;
    }  
  }
  
  if((red_step != 0 && inData[0] == 0)||(green_step != 0 && inData[1] == 0) ||(blue_step != 0 && inData[2] == 0)){
    up = true;
    
  } else if(((red_step != 0 && inData[0] == 255)||(green_step != 0 && inData[1] == 255) ||(blue_step != 0 && inData[2] == 255))) {
    up = false;
    index++;
  }

  if(active) { 
    setColor(inData[0], inData[1], inData[2]);
  }
  
  delay(led_delay);

}

void transition(int red, int green, int blue) {
  boolean end_state = false;
  
  while(end_state == false) {
    
    if(red > inData[0]) {
      inData[0]++;
    } else if(red < inData[0]) {
      inData[0]--;
    }
    if(green > inData[1]) {
      inData[1]++;
    } else if(green < inData[1]) {
      inData[1]--;
    }
    if(blue > inData[2]) {
      inData[2]++;
    } else if(blue < inData[2]) {
      inData[2]--;
    }
    
    Serial.println(inData[0]);
    
    setColor(inData[0], inData[1], inData[2]);
    delay(20);
    
    if(inData[0] == red && inData[1] == green && inData[2] == blue){
      end_state = true;
    }
  }
}
 
void setColor(int red, int green, int blue)
{
  //Serial.println(red);
  int i;
  for (i=0; i < strip.numPixels(); i++) {
      strip.setPixelColor(i, Color(green, blue, red));  
  }
   strip.show();
}

// Create a 24 bit color value from R,G,B
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

void serialEvent() {
  boolean on = false;
  while (Serial.available()) {
    // get the new byte:

    char inChar = (char)Serial.read(); 
    // add it to the inputString:
    
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
      stringComplete = true;
     
    } 
    if(!stringComplete)
      serialCommand += inChar;
  }
}
