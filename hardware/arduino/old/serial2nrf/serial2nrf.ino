#include <SPI.h>
#include "nRF24L01.h"
#include "RF24.h"
#include "printf.h"

#define RF_SETUP 0x17

String serialCommand = "";
boolean stringComplete = false;
char msg[6] = {'h', 'e', 'l', 'l', 'o'};

//CE, CSN
RF24 radio(8,7);

const uint64_t pipes[1] = { 0xF0F0F0F0D1LL };

char receivePayload[32];
uint8_t counter=0;


void setup(){
  Serial.begin(57600);
  serialCommand.reserve(200);

  printf_begin();
  radio.begin();

  // Enable this seems to work better
  radio.enableDynamicPayloads();

  radio.setDataRate(RF24_1MBPS);
  radio.setPALevel(RF24_PA_MAX);
  radio.setChannel(76);
  radio.setRetries(15,15);

  radio.openWritingPipe(pipes[0]); 
  radio.openReadingPipe(1,pipes[0]); 

      
  // Send only, ignore listening mode
  //radio.startListening();
  radio.stopListening();

  // Dump the configuration of the rf unit for debugging
  radio.printDetails(); 
  delay(1000); 

}

void loop() {
  // print the string when a newline arrives:
  
  if (stringComplete) {
    int separator = serialCommand.indexOf(":");
    if(separator != -1){
      Serial.println("node: " + serialCommand.substring(0,separator));
      Serial.println("Command: " + serialCommand.substring(separator+1, serialCommand.length()));
      sendRF(serialCommand);
      serialCommand = "";
      stringComplete = false;
    }
  }
  
}

void serialEvent() {
  boolean on = false;
  while (Serial.available()) {
    // get the new byte:

    char inChar = (char)Serial.read(); 
    // add it to the inputString:
    Serial.println(inChar, DEC);
    Serial.println(inChar);
    serialCommand += inChar;
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    if (inChar == '\n') {
      stringComplete = true;
    } 
  }
}

void sendRF(String message){ 
  char outBuffer[64] = "";// Clear the outBuffer before every loop
  message.toCharArray(outBuffer, sizeof(outBuffer));
  // Send to node
  if ( radio.write( outBuffer, sizeof(outBuffer)) ) {
    Serial.println("Send successful"); 
   }
   else {
       Serial.println("Send failed"); 
    }
    
   //radio.startListening();
  delay(1000);
   //radio.stopListening();
}
