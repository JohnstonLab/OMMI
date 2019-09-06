#include <Cyclops.h>
#include <vector>
//dual LED triggering

int exposure=5;      //exposure of the camera sensor
int incomingByte;    // a variable to read incoming serial data into
int frameCounter =0; // Count the frame acuired, use to read thru LED list
std::vector<int> ledList; // initialize a in vector of non-determinated size
int listSize =0; 

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
    // All action in the interrupt handler, just serial listening for set up
    if (Serial.available() > 0) {
      // read the oldest byte in the serial buffer:
      incomingByte = Serial.read();
      
      // if it's a capital E, it recepts the exposure
      if (incomingByte == 'E') {
        exposure = Serial.parseInt();
        //delay(100); //Python must to have time to read the info
        //Serial.println(exposure);
        //delay(100);
      }
      
      // if it's an L (ASCII 76), it recepts the LED list
      if (incomingByte == 'L') {
        //Clear the old LED list and reset frame counter
        ledList.clear(); frameCounter=0;
        
        //Append the ledList
        listSize = Serial.parseInt();
        Serial.println(listSize);
        for(int i = 0; i < listSize; ++i){
            delay(100); //ensure that python software has send the inforomation
            incomingByte = Serial.read();
            ledList.push_back(incomingByte);
            Serial.println(ledList[i]);
        }
        /*ledList = tempLedList;
        for(int i = 0; i < listSize; ++i){
            Serial.print("Element nb ");Serial.print(i);Serial.print(" : ");
            Serial.println(ledList[i]);
        }*/
      }
    }
}

void triggerEventRising()
{
  Serial.print("frameCounter =");
  Serial.println(frameCounter);
  Serial.print("modulus =");
  Serial.println(frameCounter%listSize);
  Serial.print("Stored number =");
  Serial.println(ledList[frameCounter%listSize]);
  if((ledList[frameCounter%listSize])== 'r')    //ONLY DIFF WITH green.ino (and blue.ino), READING THE GOOD CHAR IN LIST
  {
    cyclops0.dac_load_voltage(voltage); //Turn green LED ON
    delay(exposure);
    cyclops0.dac_load_voltage(0); //Turn green LED OF
  }
  frameCounter+=1; //Eaching rising edge correspond to a frame acquisition
}


