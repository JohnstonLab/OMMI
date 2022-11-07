#include <Cyclops.h>
#include <vector>
//dual LED triggering

int ledDriver = 0; //This script will be uploaded on the RED(0) LED DRIVER
int msIllumTime = 5 ; //ms component of the illumination time
int usIllumTime = 0; //us component
int incomingByte;    // a variable to read incoming serial data into
int frameCounter =0; // Count the frame acquired
int voltage = 4095; //5V set at Cyclops DAC output

//Initialization of variables for a specific mode
std::vector<int> ledList; // initialize a int vector of non-determined size
int listSize =0; 

int greenFrameInterval;

//RB mode : acquisition always begin with a red LED ON
bool red=true;
bool blue=false;


// Create a single cyclops object. CH0 corresponds to a physical board with
// jumper pads soldered so that OC0, CS0, TRIG0, and A0 are used.
// And limit current 500 mA
// Because LED is limited to 500 mA : https://www.thorlabs.com/thorproduct.cfm?partnumber=M810L3
Cyclops cyclops0(CH0, 500);


void setup()
{
  Cyclops::begin(); // start the cyclops device
  cyclops0.dac_load_voltage(0); // set the DAC output at 0V
  cyclops0.set_trigger( triggerEventRising, RISING); // cyclops trigger on rising edges
  
  // initialize serial communication:
  Serial.begin(9600);
  Serial.setTimeout(100);

}

void loop()
{
    // All action in the interrupt handler, just serial listening for set up
    if (Serial.available() > 0) {
      // read the oldest byte in the serial buffer:
      incomingByte = Serial.read();
      
      // if it's a capital C, it ensure the Connection
      // the arduino responds with its LED number allowing the right connection
      // with the python software
      if (incomingByte == 'C'){
        Serial.println(ledDriver);  
      }
      
      // if it's a capital E, it sets the exposure
      else if (incomingByte == 'E') {
        msIllumTime = Serial.parseInt();
        //delay(100);//ensure that python software is ready to receive the information
        Serial.println(msIllumTime);

        usIllumTime = Serial.parseInt();
        //delay(100);//ensure that python software is ready to receive the information
        Serial.println(usIllumTime);
      }

      /// Quick communication exchnage ///
      else if(incomingByte == 'R'){
          ledList.clear();
          listSize = 1;
          ledList.push_back(0); //Put red only in the sequence list
          //Set the acquisition mode
          cyclops0.set_trigger( rgbModeFct, RISING); // cyclops trigger on rising edges
      }
      else if(incomingByte == 'G'){
          ledList.clear();
          listSize = 1;
          ledList.push_back(1); //Put green only in the sequence list
          //Set the acquisition mode
          cyclops0.set_trigger( rgbModeFct, RISING); // cyclops trigger on rising edges
      }
      else if(incomingByte == 'B'){
          ledList.clear();
          listSize = 1;
          ledList.push_back(2); //Put blue only in the sequence list
          //Set the acquisition mode
          cyclops0.set_trigger( rgbModeFct, RISING); // cyclops trigger on rising edges
      }
      else if(incomingByte == 'N'){
          //Connect the trigger event function to "lightless" function
          cyclops0.set_trigger(triggerEventRising, RISING);
      }
      else if(incomingByte == 'Z'){
        //Reset the frame counter to prepare next acquisition (with same parameters)
        frameCounter=0;
      }

      /// Acquisition mode information section ///
      else if(incomingByte == 'M'){
        // Setting the alternation mode of the LED
        frameCounter=0; red = true; blue = false; //Reset default parameters
        delay(100);//ensure that python software has send the inforomation
        incomingByte = Serial.read();

        
      
        // if it's an L (ASCII 76), it sets the LED list
        if (incomingByte == 'L') {
          //Clear the old LED list and sets the alternation mode
          if(!ledList.empty()){ledList.clear();} 
          
          //Append the ledList
          listSize = Serial.parseInt();
          Serial.println(listSize);
          for(int i = 0; i < listSize; ++i){
              incomingByte = Serial.parseInt();
              ledList.push_back(incomingByte);
              Serial.println(ledList[i]);
          //Set the acquisition mode
          cyclops0.set_trigger( rgbModeFct, RISING); // cyclops trigger on rising edges
          }
        }
        else if(incomingByte =='G'){
          //receive green frames interval
          greenFrameInterval = Serial.parseInt();
          cyclops0.set_trigger( rbModeFct, RISING); // cyclops trigger on rising edges
          Serial.println(greenFrameInterval);
        }
        else if(incomingByte =='R'){
          //receive green frames interval
          greenFrameInterval = Serial.parseInt();
          cyclops0.set_trigger( redModeFct, RISING); // cyclops trigger on rising edges
          Serial.println(greenFrameInterval);
        }
        else if(incomingByte =='B'){
          //receive green frames interval
          greenFrameInterval = Serial.parseInt();
          cyclops0.set_trigger( blueModeFct, RISING); // cyclops trigger on rising edges
          Serial.println(greenFrameInterval);
        }
        
      }
    }
}

void triggerEventRising()
{
  
  Serial.println("Rising edge detected");
  
  frameCounter+=1; //Each rising edge corresponds to a frame acquisition
}

void rgbModeFct()
{
  if((ledList[frameCounter%listSize])== ledDriver)   //ONLY DIFF WITH green.ino (and blue.ino), READING THE GOOD CHAR IN LIST
  {
    cyclops0.dac_load_voltage(voltage); //Turn red LED ON
    delay(msIllumTime);
    delayMicroseconds(usIllumTime);
    cyclops0.dac_load_voltage(0); //Turn red LED OFF
  }
  frameCounter+=1; //Each rising edge corresponds to a frame acquisition
}

void rbModeFct()
{
  if(frameCounter%greenFrameInterval == 0){
    //turn green LED ON and OFF 
  }
  else{
    if(red){
      cyclops0.dac_load_voltage(voltage); //Turn red LED ON
      delay(msIllumTime);
      delayMicroseconds(usIllumTime);
      cyclops0.dac_load_voltage(0); //Turn red LED OFF
      red=!red;
    }
    else{
      //turn blue LED ON and OFF
      red=!red;
    }
  }
  frameCounter+=1; //Each rising edge corresponds to a frame acquisition
}

void redModeFct()
{
  if(frameCounter%greenFrameInterval == 0){
    //turn green LED ON and OFF 
  }
  else{
    cyclops0.dac_load_voltage(voltage); //Turn red LED ON
    delay(msIllumTime);
    delayMicroseconds(usIllumTime);
    cyclops0.dac_load_voltage(0); //Turn red LED OFF
  }
  frameCounter+=1; //Each rising edge corresponds to a frame acquisition
}

void blueModeFct()
{
  //Nothing to do
  frameCounter+=1; //Each rising edge corresponds to a frame acquisition
}
