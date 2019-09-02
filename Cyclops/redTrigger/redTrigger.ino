#include <Cyclops.h>

//dual LED triggering

int timeDelay = 5 ; //ms

// Create a single cyclops object. CH0 corresponds to a physical board with
// jumper pads soldered so that OC0, CS0, TRIG0, and A0 are used.
// And limit current 1000 mA
Cyclops cyclops0(CH0, 1000);
                              
bool rise = false; 
bool fall = true;
int frameCounter =0; 

int voltage = 4095; //5V


void triggerEventRising()
{
  rise=!rise;
  //if (rise && fall) //green
  //if (!rise && !fall) //red
  if((frameCounter%5)==0)
  {
    cyclops0.dac_load_voltage(voltage); //Turn green LED ON
    delay(timeDelay);
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

void setup()
{
  Cyclops::begin();
  cyclops0.dac_load_voltage(0);
  cyclops0.set_trigger( triggerEventRising, RISING);
  //cyclops0.set_trigger( triggerEventFalling, FALLING);

}

void loop()
{
    // Nothing to do, all action in the interrupt handler
}


