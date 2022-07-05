/** @file LockIn.ino
 *  @brief Compares a signal read from the LTC2500 to an internal reference signal or an external signal read from the Schmitt trigger.
 *
 *  Requires a Teensy 4.0 together with DSMV Board version 2.0
 *  Use together with the Python scripts LockIn.py and LockInGui.py.
 *  
 *  @author Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
 *  @author Philipp Rahe (prahe@uos.de)
 *  @date 04.07.2021
 *  @version 1.4
 *  
 *  @par Changelog
 *  - 04.07.2022: Fixed a bug that caused the IIR filter to shift history values before calculating,
 *                fixed a bug that caused the reference output signal to break at longer time values due to float inaccuracy
 *  - 29.06.2022: Moved filters to individual files and made them configurable via USB-protocol,
 *                Added command for sending data to PC to USB protocol,
 *                translated documentation to English
 *  - 31.03.2022: Increased maximum filter order to 100, various bug fixes, removed deprecated code
 *  - 09.07.2021: Added external reference signal
 *  - 15.02.2021: initial version
 * 
 *  @copyright 
 *  Copyright 2021 Lukas Freudenberg, Philipp Rahe 
 * 
 *  @par License
 *  @parblock
 *  Permission is hereby granted, free of charge, to any person 
 *  obtaining a copy of this software and associated documentation 
 *  files (the "Software"), to deal in the Software without 
 *  restriction, including without limitation the rights to use, copy,
 *  modify, merge, publish, distribute, sublicense, and/or sell 
 *  copies of the Software, and to permit persons to whom the Software 
 *  is furnished to do so, subject to the following conditions:
 *
 *  The above copyright notice and this permission notice shall be 
 *  included in all copies or substantial portions of the Software.
 *
 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 *  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
 *  OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
 *  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
 *  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
 *  WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
 *  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
 *  OTHER DEALINGS IN THE SOFTWARE.
 *  @endparblock
 * 
 */

#include <AD4020.h>
#include <LTC2500.h>
#include <AD5791.h>
#include <DSMV_Board.h>

float offsetLTC2500 = 0;  /**< Offset for the LTC2500 (raw value). */
float gainLTC2500 = 1.0;  /**< Gain factor for the LTC2500. */

bool blinker = false; /**< Specifies usage of LED_1. true: 1s interval (Note: This deactivates the analog output!). false: loop duration. */

#define risingFlank 0               /**< Trigger on rising flank. */
#define fallingFlank 1              /**< Trigger on falling flank. */
#define RES_LTC2500 0.0000011920929 /**< Resolution of the LTC2500. */
#define samplefreq 40000            /**< Rate (Hz) for reading and processing values. */
#define LTC2500mode noLatencyOutput /**< Specifies the output mode of the LTC2500. */

// Types of commands
#define INVALID -1    /**< Invalid command. */
#define cmdSet 0      /**< Command for setting a parameter. */
#define cmdGet 1      /**< Command for getting a parameter. */
#define cmdRequest 2  /**< Command for requesting data to be sent to the PC. */

// Settings and values
#define settingReffreq 1          /**< Setting for the frequence of the internal reference signal. */
#define settingPhaseoffset 2      /**< Setting for the phase offset. */
#define settingSource 3           /**< Setting for the reference signal source. */
#define settingFilter 4           /**< Setting for the filter type. */
#define settingFilterProperty1 5  /**< Setting for the (1st) filter porperty. */
#define settingFilterProperty2 6  /**< Setting for the 2nd filter porperty. */
#define settingFilterProperty3 7  /**< Setting for the 3rd filter porperty. */
#define settingFilterProperty4 8  /**< Setting for the 4rd filter porperty. */
#define settingFilterProperty5 9  /**< Setting for the arithmetic used by the filters. */
#define internal 1                /**< Internal reference signal. */
#define external 2                /**< External reference signal. */

const int numFilters = 2; /**< Number of filters. */
const int numProps = 6;   /**< Number of properties per filter. */

// Different filters and their default properties
#define FIRlow 0
#define defaultFIRlow {20, NULL, 10, rectWin, floatDoubleBuffer, samplefreq}
#define IIRlow 1
#define defaultIIRlow {20, NULL, NULL, NULL, NULL, samplefreq}

// Include filter functions
#include "fir.h"
#include "iir.h"

/** Array holding the properties of all filters.
 *  
 *  Note that integer values can't be bigger than 16777216 in this format due to float inaccuracy.
 */
float filterProperties[numFilters][numProps] = {
  defaultFIRlow,
  defaultIIRlow
};

int filter = IIRlow;   /**< Currently selected filter. */
//int filter = FIRlow;   /**< Currently selected filter. */

int flank = risingFlank;  /**< Specifies the flank for the frequency counter to trigger on. */
float reffreq = 500;      /**< Frequency of the internal reference signal. */
float phaseoffset = 0;    /**< Phase offset (°) of the lock in. */
int refSource = internal; /**< Reference signal source. */
float freq = 0;           /**< Measured frequency of the external reference. */
float countingfreq = 1;   /**< Frequency for updating the frequency counter. */
uint32_t crossings = 0;   /**< Number of zero crossings of the external reference in the current cycle. */

// This is where the IIR filter was previously defined

bool request = false;     /**< Specifies whether or not the PC has requested data to be sent. */
bool sampleStart = true;  /**< Specifies whether or not the sampling for the next data set has just begun. */

float voltage1 = 0; /**< Voltage of the filtered signal. */
float voltage2 = 0; /**< Voltage of the filtered phase shifted signal. */

/** @brief initialises the sketch
 */
void setup() {
  noInterrupts();                         // Prevent interrupts from triggering during setup
  setOutputPins();                        // Configure pins of the board
  AD5791initialize(-10, 10);              // Initialize AD5791
  T4TimerInit();                          // Initialize timer counter
  updateFilter();                         // Initialize filter coefficients
  LTC2500initialize(LTC2500mode, false);  // Initialize LTC2500
  T4setInterrupt1(inputFilterOutput);     // Set the ISR (interrupt service routine) for ADC reading, processing and output of the reference signal
  T4interSetup(GPT1, 1.0 / samplefreq);   // Set the interval for the read interrupt
  T4setInterrupt2(counter);               // Set the ISR for frequency counting
  T4interSetup(GPT2, 1.0 / countingfreq); // Set the interval for frequency counting
  // Activate pin-interrupt based on selected flank
  switch(flank) {
    case risingFlank:   attachInterrupt(digitalPinToInterrupt(SCHMITT_TRIGGER), count, RISING);
                        break;
    case fallingFlank:  attachInterrupt(digitalPinToInterrupt(SCHMITT_TRIGGER), count, FALLING);
                        break;
  }
  T4addSerialFunc(checkUpdateUSB);        // Set the function to check the serial port for commands
  interrupts();                           // Setup complete, activate interrupts
}

/** @brief Main loop function
 */
void loop() {
  for(int i=0; i<200; i++) {
    T4checkSerialBuffer();
    sendDataToPC();
    delay(1);
  }
  if(!blinker) {blinking();}
}

/** @brief Toggling the LED_1 to indicate that the program is still running correctly
 */
void blinking() {
  T4toggle(LED_1);
}

/** @brief Interrupt routine for recognizing the zero crossing
 */
void count() {
  crossings++;
}

/** @brief Interrupt routine for calculating the frequency
 */
void counter() {
  freq = countingfreq * crossings;
  crossings = 0;
  if(refSource == external) {
    //T4pln(freq);
    reffreq = freq;
    T4toggle(LED_1);
  }
}

/** @brief Calculates the filter coefficients
 */
void updateFilter() {
  switch(filter) {
    case FIRlow:  init_fir(FIRlow, filterProperties[FIRlow]);
                  break;
    case IIRlow: init_iir(filterProperties[IIRlow]);
                  break;
  }
}

/** @brief Interrupt routine for the Lock-In amplifier
 */
void inputFilterOutput() {
  // Start ISR timing
  T4dw(LED_3, HIGH); 
  // Read most recent value
  int32_t value1 = LTC2500readValue();
  // Offset/gain correction
  float value = value1 * gainLTC2500 + offsetLTC2500;
  // Calculate the current values of the reference and shifted reference signal
  double t = fmod(T4getTime(), (double) 1.0/reffreq);
  
  float refSig = sin(2*PI*reffreq*t+phaseoffset/360.0*2*PI);
  float refSigOut = sin(2*PI*reffreq*t);
  float refSigShift = sin(2*PI*reffreq*t+(phaseoffset-90.0)/360.0*2*PI);
  // Output the current value of the reference signal times 5 (why do we do this again?)
  AD5791setVoltage(5.0*refSigOut);
  // Arrays to hold input values for filters
  float values[2] = {value * refSig, value * refSigShift};
  int32_t valuesRaw[2] = {value * refSig, value * refSigShift};
  // Array for filtered values
  float* filtered;
  // Apply low pass filter
  T4dw(LED_2, HIGH);  
  switch(filter) {
    case IIRlow:  filtered = proc_iir(values, filterProperties[filter]);
                  break;
    case FIRlow:  filtered = proc_fir(values, valuesRaw, filterProperties[filter]);
                  break;
    case INVALID: filtered = values;
                  break;
  }
  // Convert values into voltages and divide values by half factor of the filter
  voltage1 = filtered[0] * RES_LTC2500 * 2;
  voltage2 = filtered[1] * RES_LTC2500 * 2;
  // Stop ISR timing
  T4dw(LED_3, LOW); 
}

/** @brief Sends buffers to PC once they are full
 */
void sendDataToPC() {
  sampleStart = true;
  // If the PC hasn't requested any data, it is discarded.
  if(!request) {return;}
  T4sw(T4toBytes(voltage1), 4);
  T4sw(T4toBytes(voltage2), 4);
  if(refSource == external) {
    T4sw(T4toBytes(freq), 4);
  }
  request = false;
}

/** @brief Maps the ASCII commands to IDs.
 *
 *  Currently implemented are the maps:
 *
 *  LockIn.set  ->  cmdSet
 *  LockIn.get  ->  cmdGet
 *  send data   ->  cmdRequest
 *  
 *  @param command Command (in ASCII format) as received from PC
 *  @return numerical identifier for the respective command.  
 */
int checkCommand(String command) {
  if(command.startsWith("LockIn.set ")) {return cmdSet;}
  if(command.startsWith("LockIn.get ")) {return cmdGet;}
  if(command.startsWith("send data"))   {return cmdRequest;}
  return INVALID;
}

/** @brief Maps the ASCII commands to IDs.
 *
 *  Currently implemented are the maps:
 *
 *  Internal  ->  internal
 *  External  ->  external
 *  
 *  @param command Command (in ASCII format) as received from PC
 *  @return numerical identifier for the respective command.  
 */
int checkSource(String a) {
  if(a.startsWith("Internal")) {return internal;}
  if(a.startsWith("External")) {return external;}
  return INVALID;
}

/** @brief Maps the ASCII commands to IDs.
 *
 *  Currently implemented are the maps:
 *
 *  reffreq             ->  settingReffreq
 *  phaseOffset         ->  settingPhaseoffset
 *  source              ->  settingSource
 *  filter              ->  settingFilter
 *  set filterProperty1 ->  settingFilterProperty1
 *  set filterProperty2 ->  settingFilterProperty2
 *  set filterProperty3 ->  settingFilterProperty3
 *  set filterProperty4 ->  settingFilterProperty4
 *  set filterProperty5 ->  settingFilterProperty5
 *  
 *  @param command Command (in ASCII format) as received from PC
 *  @return numerical identifier for the respective command.  
 */
int checkSetting(String command) {
  if(command.startsWith("reffreq"))           {return settingReffreq;}
  if(command.startsWith("phaseOffset"))       {return settingPhaseoffset;}
  if(command.startsWith("source"))            {return settingSource;}
  if(command.startsWith("filter "))           {return settingFilter;}
  if(command.startsWith("filterProperty1 "))  {return settingFilterProperty1;}
  if(command.startsWith("filterProperty2 "))  {return settingFilterProperty2;}
  if(command.startsWith("filterProperty3 "))  {return settingFilterProperty3;}
  if(command.startsWith("filterProperty4 "))  {return settingFilterProperty4;}
  if(command.startsWith("filterProperty5 "))  {return settingFilterProperty5;}
  return INVALID;
}

/** @brief Maps the ASCII commands to filter IDs.
 *
 *  Currently implemented are the maps:
 *  
 *  FIR low pass filter ->  FIRlow
 *  IIR low pass filter ->  IIRlow
 *
 *  @param command Command (in ASCII format) as received from PC
 *  @return numerical identifier for the respective filter.  
 */
int checkFilter(String command) {
  if(command.startsWith("FIR low pass filter"))       {return FIRlow;}
  if(command.startsWith("IIR low pass filter"))       {return IIRlow;}
  return INVALID;
}

/** @brief Maps the ASCII command for windows to IDs.
 *
 *  Currently implemented are the maps:
 *
 *  Rectangle ->  rectWin
 *  Hamming   ->  hamminWin
 *
 *  @param command Window names (in ASCII format) as received from PC
 *  @return numerical identifier for the respective window.
 */
int checkWindow(String command) {
  if(command.startsWith("Rectangle")) {return rectWin;}
  if(command.startsWith("Hamming"))   {return hammingWin;}
  return INVALID;
}

/** @brief Maps the ASCII command for arithmetics to IDs.
 *
 *  Currently implemented are the maps:
 *
 *  Integer double buffer ->  integerDoubleBuffer
 *  Integer if modulo     ->  integerIfModulo
 *  Integer modulo        ->  integerModulo
 *  Float double buffer   ->  floatArithmetic
 *  Float if modulo       ->  floatIfModulo
 *  Float modulo          ->  floatModulo
 *
 *  @param command Window names (in ASCII format) as received from PC
 *  @return numerical identifier for the respective window.
 */
int checkArithmetic(String command) {
  if(command.startsWith("Integer double buffer")) {return integerDoubleBuffer;}
  if(command.startsWith("Integer if modulo"))     {return integerIfModulo;}
  if(command.startsWith("Integer modulo"))        {return integerModulo;}
  if(command.startsWith("Float double buffer"))   {return floatDoubleBuffer;}
  if(command.startsWith("Float if modulo"))       {return floatIfModulo;}
  if(command.startsWith("Float modulo"))          {return floatModulo;}
  return INVALID;
}

/** @brief Processes commands received from the PC
 *
 *  @param command Command (in ASCII format) as received from PC
 *  @return false if an invalid command has been received. Otherwise true. 
 */
bool checkUpdateUSB(String command) {
  bool b = false;
  switch(checkCommand(command)) {
    case cmdSet:      command.remove(0, 11);
                      switch(checkSetting(command)) {
                        case INVALID:             break;
                        case settingReffreq:      b = true;
                                                  switch(refSource) {
                                                    case internal:  {
                                                                    command.remove(0, 8);
                                                                    float val = command.toFloat();
                                                                    if(val <= 0) {
                                                                      break;
                                                                    }
                                                                    reffreq = val;
                                                                    break;
                                                    }
                                                    case external:  break;
                                                  }
                        case settingPhaseoffset: {
                                                  command.remove(0, 12);
                                                  float val = command.toFloat();
                                                  if(val < -180 || val > 180) {
                                                    break;
                                                  }
                                                  phaseoffset = val;
                                                  b = true;
                                                  break;
                        }
                        case settingFilter:         command.remove(0, 7);
                                                    switch(checkFilter(command)) {
                                                      case FIRlow:    filter = FIRlow;
                                                                      b = true;
                                                                      break;
                                                      case IIRlow:   filter = IIRlow;
                                                                      b = true;
                                                                      break;
                                                    }
                                                    updateFilter();
                                                    break;
                        case settingFilterProperty1:command.remove(0, 16);
                                                    filterProperties[filter][0] = command.toFloat();
                                                    updateFilter();
                                                    b = true;
                                                    break;
                        case settingFilterProperty2:command.remove(0, 16);
                                                    filterProperties[filter][1] = command.toFloat();
                                                    updateFilter();
                                                    b = true;
                                                    break;
                        case settingFilterProperty3:{
                                                      command.remove(0, 16);
                                                      uint16_t Mfilter = min(max(command.toInt(), 0) / 2, MfilterMax);
                                                      uint16_t Nfilter = 2*Mfilter + 1;
                                                      filterProperties[filter][2] = Nfilter;
                                                      updateFilter();
                                                      b = true;
                                                      break;
                                                    }
                        case settingFilterProperty4:command.remove(0, 16);
                                                    switch(checkWindow(command)) {
                                                      case rectWin:     filterProperties[filter][3] = rectWin;
                                                                        init_fir(filter, filterProperties[filter]);
                                                                        return true;
                                                                        break;
                                                      case hammingWin:  filterProperties[filter][3] = hammingWin;
                                                                        init_fir(filter, filterProperties[filter]);
                                                                        return true;
                                                                        break;
                                                    }
                                                    return true;
                                                    break;
                        case settingFilterProperty5:command.remove(0, 16);
                                                    switch(checkArithmetic(command)) {
                                                      case integerDoubleBuffer: filterProperties[filter][4] = integerDoubleBuffer;
                                                                                b = true;
                                                                                break;
                                                      case integerIfModulo:     filterProperties[filter][4] = integerIfModulo;
                                                                                b = true;
                                                                                break;
                                                      case integerModulo:       filterProperties[filter][4] = integerModulo;
                                                                                b = true;
                                                                                break;
                                                      case floatDoubleBuffer:   filterProperties[filter][4] = floatDoubleBuffer;
                                                                                b = true;
                                                                                break;
                                                      case floatIfModulo:       filterProperties[filter][4] = floatIfModulo;
                                                                                b = true;
                                                                                break;
                                                      case floatModulo:         filterProperties[filter][4] = floatModulo;
                                                                                b = true;
                                                                                break;
                                                      case INVALID:             break;
                                                    }
                                                    break;
                        }
                        case settingSource:       command.remove(0, 7);
                                                  switch(checkSource(command)) {
                                                    case internal:  refSource = internal;
                                                                    b = true;
                                                                    break;
                                                    case external:  refSource = external;
                                                                    b = true;
                                                                    break;
                                                  }
                                                  break;
                      break;
    case cmdGet:      command.remove(0, 11);
                      T4p("Getting parameter: " + command + "; ");
                      //int setting = checkSetting(command); // Check which parameter to get
                      switch(checkSetting(command)) {
                        case INVALID:                 T4pln("Parameter doesn't exist.");
                                                      break;
                        case settingReffreq: {
                                                      T4p("Reference frequency: ");
                                                      T4p(reffreq);
                                                      T4pln("Hz");
                                                      b = true;
                                                      break;
                        }
                        case settingPhaseoffset:      b = true;
                                                      T4p("Phase offset: ");
                                                      T4p(phaseoffset);
                                                      T4pln("Hz");
                                                      break;
                        case settingFilterProperty1:  b = true;
                                                      T4p("Cutoff frequency: ");
                                                      T4p(filterProperties[filter][0]);
                                                      T4pln("Hz");
                                                      break;
                        case settingFilterProperty3:  b = true;
                                                      T4p("Filter Order: ");
                                                      T4pln(filterProperties[filter][2] - 1);
                                                      break;
                        case settingFilterProperty4:  b = true;
                                                      T4p("Filter Window: ");
                                                      T4pln(filterProperties[filter][3] - 1);
                                                      break;
                        case settingFilterProperty5:  b = true;
                                                      T4p("FIR filter arithmetic: ");
                                                      T4pln(filterProperties[filter][4] - 1);
                                                      break;
                        case settingSource:           b = true;
                                                      T4p("Reference source: ");
                                                      switch(refSource) {
                                                        case internal:  T4pln("internal");
                                                                        break;
                                                        case external:  T4pln("external");
                                                                        break;
                                                      }
                                                      break;
                      }
    case cmdRequest:  request = true;
                      return true;
                      break;
    case INVALID:     T4pln(command);
                      return false;
                      break;
  }
  return b;
}
