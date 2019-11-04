

/* BladderTracker Pressure Monitor Code */

/*
  This code was written by Calum Wilson with help from Penny Lawton.

*/

// First thing's first, link to the required libraries:

#include <WheatstoneBridge.h> // Include the Wheatstone library
#include <LiquidCrystal.h> // Include the LCD library
#include "strain_gauge_shield_and_lcd_support_functions.h" // Include support function header ---> This file should be in the working folder!

// Initialize the library with the numbers of the interface pins
LiquidCrystal lcd(8, 9, 4, 5, 6, 7);

// Initial calibration values
const int CST_PRESSURE_IN_MIN = 350;       // Raw value calibration lower point
const int CST_PRESSURE_IN_MAX = 650;       // Raw value calibration upper point
const int CST_PRESSURE_OUT_MIN = 0;        // Pressure calibration lower point
const int CST_PRESSURE_OUT_MAX = 200;     // Pressure calibration upper point ---> 140 is about the maximum that can be read out with the default gain on the RB-Onl-38 and 26PCDFG5G pressure transducers. Can change the gain with surface mount resistors.

const int CST_CAL_PRESSURE_MIN = 0;
const int CST_CAL_PRESSURE_MAX = 200;
const int CST_CAL_PRESSURE_STEP = 5;
const int CST_CAL_PRESSURE_STEP_LARGE = 10;

// Initialize the first Wheatstone bridge object
WheatstoneBridge wsb_pressure1(A1, CST_PRESSURE_IN_MIN, CST_PRESSURE_IN_MAX, CST_PRESSURE_OUT_MIN, CST_PRESSURE_OUT_MAX);

// Initialize the second Wheatstone bridge object
WheatstoneBridge wsb_pressure2(A0, CST_PRESSURE_IN_MIN, CST_PRESSURE_IN_MAX, CST_PRESSURE_OUT_MIN, CST_PRESSURE_OUT_MAX);



// < Setup function >
void setup()
{
  // Initialize LCD screen
  lcd.begin(16, 2);
  
  // Intro screen
  displayScreen("BladderTracker", "Pressure Monitor");
  delay(3000);

  //Calibrate the first pressure transducer!
  // Calibration
  displayScreen("* Calibration *", "Transducer 1");
  delay(2000);
  
  // Calibration - Low value
  displayScreen("* Calibration *", "Low value");
  delay(2000);
  
  // Calibration - linear interpolation
  int cal_adc_low = CST_PRESSURE_IN_MIN;
  int cal_adc_high = CST_PRESSURE_IN_MAX;
  int cal_pressure_low = CST_PRESSURE_OUT_MIN;
  int cal_pressure_high = CST_PRESSURE_OUT_MAX;
  
  // Calibration - Low value
  displayScreen("* Calibration *", "Low value");
  //Serial.println("* Calibration * - Low value");
  delay(1000);
  // Get force value
  cal_pressure_low = getValueInRange("Set low pressure", "Pres (mmHg):", 13, cal_pressure_low, CST_CAL_PRESSURE_MIN, CST_CAL_PRESSURE_MAX, CST_CAL_PRESSURE_STEP, CST_CAL_PRESSURE_STEP_LARGE);
  // Get ADC raw value
  cal_adc_low = getValueADC("Set low raw ADC", "Raw ADC:", 13, A1, btnSELECT);
  
  // Calibration - High value
  displayScreen("* Calibration *", "High value");
  //Serial.println("* Calibration * - High value");
  delay(1000);
  // Get force value
  cal_pressure_high = getValueInRange("Set high pressure", "Pres (mmHg):", 13, cal_pressure_high, CST_CAL_PRESSURE_MIN, CST_CAL_PRESSURE_MAX, CST_CAL_PRESSURE_STEP, CST_CAL_PRESSURE_STEP_LARGE);
  // Get ADC raw value
  cal_adc_high = getValueADC("Set high raw ADC", "Raw ADC:", 13, A1, btnSELECT);
  
  //Perform calibration
  wsb_pressure1.linearCalibration(cal_adc_low, cal_adc_high, cal_pressure_low, cal_pressure_high);

  // Setup display labels
  displayScreen("P1 (mmHg):", "P2 (mmHg): N/A");
  Serial.begin(9600);

}

// Timing management
long display_time_step = 10;
long display_time = 0;

// Force measurement & display
int pressure_adc;
int pressure;
int pressure_adc2;
int pressure2;
int force_pos_offset;

#define NUMSAMPLES 1
uint16_t samples[NUMSAMPLES];
uint16_t samples2[NUMSAMPLES];
uint8_t i;
float average;
float average2;

int count = 1;
// < Main code >
void loop(){

    //Measure from the first pressure transducer
    // Make a force measurement and obtain the calibrated force value


   

    average = wsb_pressure1.measureForce();

    // Display raw ADC value
    //lcd.setCursor(11, 0); lcd.print("       ");
    

    if (count == 40){
      lcd.setCursor(11, 0); lcd.print("       ");
      lcd.setCursor(11, 0); lcd.print(average,2);
      count = 1;
    }
    count = count+1;

    // Print to the serial Port
    // Do not change this, as it needs to be this format for VasoTracker
    Serial.print("<P1");
    Serial.print(":");
    Serial.print(average,2);
    Serial.print(";");
    
    Serial.print("P2");
    Serial.print(":");
    Serial.print(average,2);
    Serial.print(";");
    
    Serial.println(">");
    Serial.flush();


    
  
}
