#include <Cyclops.h>

//dual LED triggering

int msIllumTime = 5 ; //ms component
int usIllumTime = 0; //us component
int incomingByte;      // a variable to read incoming serial data into

int greenFrameInterval;

bool rgbMode = false;
bool rbMode = false;
bool redMode = false;
bool blueMode = false;

bool red=true;
bool blue=false;

// Create a single cyclops object. CH0 corresponds to a physical board with
// jumper pads soldered so that OC0, CS0, TRIG0, and A0 are used.
// And limit current 1000 mA
Cyclops cyclops0(CH0, 1000);
                              
bool rise = false; 
bool fall = true;
int ledDriver = 0; //This script will be uploaded on the RED LED DRIVER
int frameCounter =0; 

int voltage = 4095; //5V


void triggerEventRising()
{
  //rise=!rise;
  //if (rise && fall) //green
  //if (!rise && !fall) //red
//  if((frameCounter%5)==0)
//  {
//    
//    cyclops0.dac_load_voltage(voltage); //Turn green LED ON
//    delay(msIllumTime);
//    delayMicroseconds(usIllumTime);
//    cyclops0.dac_load_voltage(0); //Turn green LED OF
//  }
  if(rbMode){rbModeFct();}
  //When cyclops detect a falling edge, call triggerEventFalling() method
  frameCounter+=1;
}
//
//void triggerEventFalling()
//{
//  fall=!fall;
//  cyclops0.set_trigger( triggerEventRising, RISING);
//  
//}

void setup()
{
  Cyclops::begin();
  cyclops0.dac_load_voltage(0);
  cyclops0.set_trigger( triggerEventRising, RISING);
  //cyclops0.set_trigger( triggerEventFalling, FALLING);

  // initialize serial communication:
  Serial.begin(9600);

}

void loop()
{
    // Nothing to do, all action in the interrupt handler

    if (Serial.available() > 0) {
      // read the oldest byte in the serial buffer:
      incomingByte = Serial.read();
      if (incomingByte == 'C'){
        Serial.println(ledDriver);  
      }

      else if (incomingByte == 'E') {
        msIllumTime = Serial.parseInt();
        delay(100); //Python must to have time to read the info
        Serial.println(msIllumTime);
        delay(100);

        usIllumTime = Serial.parseInt();
        delay(100); //Python must to have time to read the info
        Serial.println(usIllumTime);
        delay(100);
        
        //Turn on the LED to check the value sent
        cyclops0.dac_load_voltage(voltage); //Turn green LED ON
        delay(msIllumTime);
        delayMicroseconds(usIllumTime);
        cyclops0.dac_load_voltage(0); //Turn green LED OFF
      }

      else if(incomingByte == 'M'){
        // Setting the alternation mode of the LED
        frameCounter=0; red = true; blue = false; //Reset default parameters
        rgbMode = false; rbMode = false; redMode = false; blueMode = false;
        incomingByte = Serial.read();
        if(incomingByte =='L'){
          //Set to rgb mode
          rgbMode = true;
          //send list of alternation
        }
        else if(incomingByte =='G'){
          //Set to rb mode
          rbMode = true;
          greenFrameInterval = Serial.parseInt();
          //receive green frames interval
        }
        else if(incomingByte =='R'){
          //Set to redOnly mode
          redMode = true;
          //receive green frames interval
        }
        else if(incomingByte =='B'){
          //Set to blueOnly mode
          blueMode = true;
          //receive green frames interval
        }
      }
      
      // if it's a capital H (ASCII 72), turn on the LED:
      else if (incomingByte == 'H') {
        cyclops0.dac_load_voltage(voltage);
      }
      // if it's an L (ASCII 76) turn off the LED:
      else if (incomingByte == 'L') {
        cyclops0.dac_load_voltage(0);
      }
    }
}

void rbModeFct()
{
  if(frameCounter%greenFrameInterval == 0){
    //turn green LED ON  
  }
  else if(red){
    cyclops0.dac_load_voltage(voltage); //Turn red LED ON
    delay(msIllumTime);
    delayMicroseconds(usIllumTime);
    cyclops0.dac_load_voltage(0); //Turn red LED OFF
    blue=!blue;
  }
  else if(blue){
    //turn blue LED ON
    red=!red;
  }
}


