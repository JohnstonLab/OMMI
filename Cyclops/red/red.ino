#include <Cyclops.h>

//dual LED triggering

int exposure=5;      //exposure of the camera sensor
int incomingByte;    // a variable to read incoming serial data into
int frameCounter =0; // Count the frame acuired, use to read thru LED list
char* ledList; // initialize a char list of non-determinated size 

int voltage = 4095; //5V set at Cyclops DAC output

// Create a single cyclops object. CH0 corresponds to a physical board with
// jumper pads soldered so that OC0, CS0, TRIG0, and A0 are used.
// And limit current 1000 mA
Cyclops cyclops0(CH0, 1000);


void setup()
{
  Cyclops::begin(); // start the cyclops device
  cyclops0.dac_load_voltage(0); // set the DAC ouptut at 0V
  cyclops0.set_trigger( triggerEventRising, RISING); // cyclops trigger on rising edges
  
  // initialize serial communication:
  Serial.begin(9600);

}

void loop()
{
    // Nothing to do, all action in the interrupt handler
    if (Serial.available() > 0) {
      // read the oldest byte in the serial buffer:
      incomingByte = Serial.read();
      
      // if it's a capital E, it recepts the exposure
      if (incomingByte == 'E') {
        exposure = Serial.parseInt();
        Serial.println(exposure);
        if (exposure){
          cyclops0.dac_load_voltage(voltage); //Turn green LED ON
          delay(exposure*1000);
          cyclops0.dac_load_voltage(0); //Turn green LED OF
        }
        else{
          cyclops0.dac_load_voltage(voltage); //Turn green LED ON
          delay(1000);
          cyclops0.dac_load_voltage(0); //Turn green LED OF   
        }
      }
      
      // if it's an L (ASCII 76), it recepts the LED list
      if (incomingByte == 'L') {
        //Append the ledList until 'N' char (end of communication) is recepted
        int listSize = Serial.parseInt();
        char tempLedList[listSize];
        for(int i = 0; i < listSize; ++i){
            incomingByte = Serial.read();
            tempLedList[i] = static_cast<char>(incomingByte);
            Serial.println(incomingByte);
        }
        ledList = tempLedList;
        Serial.println(ledList);
      }
    }
}

void triggerEventRising()
{
  if((frameCounter%5)==0)
  {
    cyclops0.dac_load_voltage(voltage); //Turn green LED ON
    delay(exposure);
    cyclops0.dac_load_voltage(0); //Turn green LED OF
  }
  frameCounter+=1;
}


