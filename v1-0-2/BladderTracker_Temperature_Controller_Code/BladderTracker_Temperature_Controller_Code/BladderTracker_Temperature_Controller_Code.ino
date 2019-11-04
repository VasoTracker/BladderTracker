

/* VasoTracker Temperature Controller Code */

/*
  This code was written by Calum Wilson.

*/

// < Initialisation >

//#include "strain_gauge_shield_and_lcd_support_functions.h" // Include support function header ---> This file should be in the working folder!
#include <LiquidCrystal.h> // Include the LCD library

LiquidCrystal lcd(8, 9, 4, 5, 6, 7); // Initialize the library with the numbers of the interface pins
#define btnRIGHT 0
#define btnUP 1
#define btnDOWN 2
#define btnLEFT 3
#define btnSELECT 4
#define btnNONE 5
#define btnUNKNOWN 6

//Define Variables and settings we'll be using
#define thermistor_pin A0 // which analog thermistor input pin
#define nominal_temp 25 // nominal resistance temperature (almost always 25 C)   
#define nominal_resistance 10000 // nominal  resistance at nominal resistance temperature   
#define beta_coeff 3950 // beta coefficient of the thermistor
#define series_resistor 10000 // the value of the 'other' resistor    
#define output_pin  3
#define initial_set_point 25.0 // initial set point
#define num 10 // number of samples to take average over
uint16_t samples[num]; // array for samples
double setpoint, test, cal_temp_low;
int min_temp = 25;
int max_temp = 40;

// < Function for reading >
int readkeypad(){
  int adc_key_in = analogRead(5); //
  int ret = btnUNKNOWN;
  
  if (adc_key_in < 50) ret = btnRIGHT;
  if ( (adc_key_in > 50) && (adc_key_in < 250) ) ret = btnUP;
  if ( (adc_key_in > 250) && (adc_key_in < 450) ) ret = btnDOWN;
  if ( (adc_key_in > 450) && (adc_key_in < 650) ) ret = btnLEFT;
  if ( (adc_key_in > 650) && (adc_key_in < 850) ) ret = btnSELECT;
  if (adc_key_in > 850) ret = btnNONE; 
  return ret;
 }



// < Setup function >
void setup()
{
  // Initialize LCD screen
  lcd.begin(16, 2);
  
  // Intro screen
  //print_to_LCD("Myograph Temp","Controller");
  lcd.setCursor(0, 0); lcd.print("Myograph Temp");
  lcd.setCursor(0, 1); lcd.print("Controller");
  delay(2000);

  // Main screen
  //print_to_LCD("Set (*C):", "Act (*C):");
  lcd.setCursor(0, 0); lcd.print("Set (*C):  ");
  lcd.setCursor(0, 1); lcd.print("Act (*C):  ");
  
  Serial.begin(9600);

  // Setpoint
  setpoint = initial_set_point;

  //Set the output pin
  pinMode(output_pin, OUTPUT);
}

int count = 1;
// < Main program loop >
void loop(void) {
  
  // Take a single sample
  float ADC_average;

  ADC_average = analogRead(thermistor_pin);

  // Convert the voltage drop over the thermistor to resistance
  // Using the Steinhart equation
  // However, remember that the analogPorts don't give a voltage, but an ADC value...
  float resistance;
  float temperature;
  
  resistance = series_resistor / ((1023 / ADC_average) - 1);
  temperature = 1/( log(resistance / nominal_resistance)/beta_coeff + (1.0 / (nominal_temp + 273.15)) ) - 273.15 ;            
 

  int value = setpoint;
  int lastValue = -1;
  int buttons = btnNONE;


  // Check if any of the LCD shield buttons have been pressed
  int lcd_button_adc = analogRead(A5);
  
  int buttons2 = readkeypad();
  switch(buttons2)
  {
    case btnUP:
      setpoint += 1;
      if(setpoint > max_temp)
        setpoint = max_temp;
      break;
      
    case btnRIGHT:
      setpoint += 0.5;
      if(setpoint > max_temp)
        setpoint = max_temp;
      break;

    case btnDOWN:
      setpoint -= 1;
      if(setpoint < min_temp)
        setpoint = min_temp;
      break;

    case btnLEFT:
      setpoint -= 0.5;
      if(setpoint < min_temp)
        setpoint = min_temp;
      break;
  }

  // Display temperature values
  if (count == 40){
    lcd.setCursor(11, 0); lcd.print(setpoint);
    lcd.setCursor(11, 1); lcd.print(temperature);
    count = 1;
  }
  count = count+1;

  // Turn on/off the output pin(s)
  if (setpoint > temperature){
    digitalWrite(output_pin, HIGH);
    //Serial.print("\tHeater ON");
  } else {
    digitalWrite(output_pin, LOW);
    //Serial.print("\tHeater OFF");
  }

  // Print to the serial Port
  // Do not change this, as it needs to be this format for VasoTracker
  Serial.print("<T1");
  Serial.print(":");
  Serial.print(temperature);
  Serial.print(";");
  
  Serial.print("T2");
  Serial.print(":");
  Serial.print(temperature);
  Serial.print(";");
   
  Serial.println(">");

 
  
}



