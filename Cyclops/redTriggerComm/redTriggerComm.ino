#include <Cyclops.h>

//dual LED triggering

int exposure=0;      //exposure of the camera sensor
int incomingByte;    // a variable to read incoming serial data into

// Create a single cyclops object. CH0 corresponds to a physical board with
// jumper pads soldered so that OC0, CS0, TRIG0, and A0 are used.
// And limit current 1000 mA
Cyclops cyclops0(CH0, 1000);
                              
bool rise = false; 
bool fall = true;
int frameCounter =0; 

int voltage = 4095; //5V


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
      // if it's an L (ASCII 76) turn off the LED:
      if (incomingByte == 'L') {
        cyclops0.dac_load_voltage(0);
      }
    }
}

void triggerEventRising()
{
  //rise=!rise;
  //if (rise && fall) //green
  //if (!rise && !fall) //red
  if((frameCounter%5)==0)
  {
    cyclops0.dac_load_voltage(voltage); //Turn green LED ON
    delay(exposure);
    cyclops0.dac_load_voltage(0); //Turn green LED OF
  }
  //When cyclops detect a falling edge, call triggerEventFalling() method
  cyclops0.set_trigger( triggerEventFalling, FALLING);
  frameCounter+=1;
}

void triggerEventFalling()
{
  fall=!fall;
  cyclops0.set_trigger( triggerEventRising, RISING);
  
}


