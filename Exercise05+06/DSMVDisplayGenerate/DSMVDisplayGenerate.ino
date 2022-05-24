/** @file DisplayDSMVGenerate.ino
 *  @brief Implements the basic functionality of an oscilloscope.
 *
 *  Requires a Teensy 4.0 together with DSMV Board version 2.0
 *  Use together with the python scripts DisplayDSMV.py and 
 *  DisplayDSMVGui.py.
 *  
 *  @author Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
 *  @author Philipp Rahe (prahe@uos.de)
 *  @date 24.05.2022
 *  @version 1.7.2
 *  
 *  @par Changelog 
 *  - 24.05.2022: Reverted change of sending data in chunks
 *                as this wasn't necessary after a fix in the timing of sending data,
 *                changed USB protocol to be compatible with future python GUIs
 *  - 23.05.2022: Changed sending of data to PC to only sending chunks of 4096 bytes at a time
 *  - 20.05.2022: Added command for sending data to PC to USB protocol
 *  - 12.05.2022: Added processing rate customization to USB protocol
 *  - 06.05.2022: Changed averaging to integer arithmetic,
 *                added functionality to send raw values to the PC (controlled via USB command),
 *                corrected documentation on USB protocol
 *  - 26.01.2022: Decreased interval between processing received commands
 *  - 17.01.2022: reduced speed of sending data via USB to ensure that the new GUI can keep up
 *  - 24.05.2021: updated for spectral analysis, output signals added
 *                and fully translated documentation to English
 *  - 12.05.2020: initial version
 * 
 *  @copyright 
 *  Copyright 2022 Lukas Freudenberg, Philipp Rahe 
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

#include <LTC2500.h>
#include <AD4020.h>
#include <AD5791.h>
#include <DSMV_Board.h>

float offsetAD4020 = 0;         /**< Offset voltage for the AD4020 (this is your task). */
float gainAD4020 = 1.0;         /**< Gain factor for the AD4020 (this is your task). */
float offsetLTC2500 = 0;        /**< Offset voltage for the LTC2500 (this is your task). */
float gainLTC2500 = 1.0;        /**< Gain factor for the LTC2500 (this is your task). */
float offsetInternal = 0;       /**< Offset voltage for the internal ADC (this is your task). */
float gainInternal = 1.0;       /**< Gain factor Gain factor for the internal ADC (this is your task). */

bool blinker = false;            /**< Specifies usage of LED_1. true: 1s interval (Note: This deactivates the analog output!). false: loop duration. */

bool AD4020active = true;       /**< Specifies whether the AD4020 is being read. */
bool LTC2500active = true;      /**< Specifies whether the AD4020 is being read. */
bool INTERNALADCactive = true;  /**< Specifies whether the AD4020 is being read. */

#define RES_AD4020  0.0000190734863 /**< Resolution of the AD4020. */
#define RES_LTC2500 0.0000011920929 /**< Resolution of the LTC2500. */
#define RES_Internal 0.004884005    /**< Resolution of the internal ADC. */
#define LTC2500mode noLatencyOutput /**< Specifies the output mode of the LTC2500. */
#define FALL 0                      /**< Trigger on falling flank. */
#define RISE 1                      /**< Trigger on rising flank. */
#define WAIT 0                      /**< Waiting for trigger-signal to cross threshold. */
#define TRIGGERED 1                 /**< Threshold has been crossed and data is being recorded. */
#define HOLDING 2                   /**< Data has been recorded. Waiting for trigger singnal to reset. */
#define UNTRIGGERED 0               /**< No input selected for trigger. */
#define AD4020 1                    /**< Triggering on AD4020 and (de)activate it. */
#define LTC2500 2                   /**< Triggering on LTC2500 and (de)activate it. */
#define INTERNALADC 3               /**< Triggering on internal ADC and (de)activate it. */
#define SCHMITT 4                   /**< Triggering on the schmitt trigger. */
#define settingOversamples 0        /**< Setting for the number of oversamples: */
#define settingSize 1               /**< Setting for the data size. */
#define settingSpectralFreq 2       /**< Setting for the sampling frequency. */
#define settingProcessingFreq 3     /**< Setting for the output frequency. */
#define settingTriggerSource 4      /**< Setting for the trigger source. */
#define settingThreshold 5          /**< Setting for the voltage threshold of the trigger. */
#define settingFlank 6              /**< Setting for the trigger flank. */
#define settingMode 7           /**< Setting for activating an ADC. */
#define settingDeactivate 8         /**< Setting for deactivating an ADC. */
#define settingSignalType 9         /**< Setting for the signal type sent to the PC. */
#define commandRequest 10           /**< Command for requesting data to be sent to the PC. */
#define signalVoltage 0             /**< Voltage read from ADCs. */
#define signalRaw 1                 /**< Raw value read from ADCs. */
#define INVALID -1                  /**< Invalid command. */

const uint32_t maxLen = 4*32768;  /**< Maximum length of the data buffers in bytes. */
uint32_t bufLen = 4*100;          /**< Current length of the data buffers in bytes. */
uint8_t bufAD4020[maxLen];        /**< Data buffer for the AD4020. */
uint8_t bufLTC2500[maxLen];       /**< Data buffer for the LTC2500. */
uint8_t bufInternal[maxLen];      /**< Data buffer for the internal ADC. */
int32_t bufPos = 0;               /**< Position in the data buffers to write to. */
bool full = false;                /**< Specifies whether or not the buffer is ready to be sent to the PC. */
bool request = false;             /**< Specifies whether or not the PC has requested data to be sent. */
bool sampleStart = true;          /**< Specifies whether or not the sampling for the next data set has just begun. */
float samplerate = 1000;          /**< Sampling frequency. */
float processingRate = 1000;      /**< Frequency to output the individual signal values. */
float outputSigFreq = 4000;       /**< Frequency of the output signal. */
int oversamples = 1;              /**< Number of oversamples. */
int samples = 0;                  /**< Number of samples since last storing. */
int signalType = signalVoltage;   /**< Signal type sent to the PC. */
float voltageAD4020 = 0;          /**< Stores the current voltage value of the AD4020 */
float voltageLTC2500 = 0;         /**< Stores the current voltage value of the LTC2500 */
float voltageInternal = 0;        /**< Stores the current voltage value of the internal ADC. */
int64_t sumAD4020 = 0;            /**< Stores the current sum of the raw values of the AD4020. */
int64_t sumLTC2500 = 0;           /**< Stores the current sum of the raw values of the LTC2500. */
int64_t sumInternal = 0;          /**< Stores the current sum of the raw values of the internal ADC. */
int triggerSource = UNTRIGGERED;  /**< Trigger source. */
float triggerThreshold = 0;       /**< Voltage threshold for the trigger. */
bool triggerFlank = RISE;         /**< Flank to trigger on. */
int triggerState = WAIT;          /**< State of the trigger. */


/** @brief initialises the sketch
 */
void setup() {
  noInterrupts();                         // Prevent interrupts from triggering during setup
  setOutputPins();                        // Configure pins of the board
  digitalWrite(MOSI_ADC, HIGH);           // Set the MOSI of the ADCs to HIGH
  T4arr(12);                              // Resolution of the internal ADC is 12 bit
  T4aravg(1);                             // Every sample of the internal ADC is being read by itself
  T4awr(12);                              // Resolution of the PWM outputs set to 12 bit
  T4TimerInit();                          // Initialize timer counter
  AD4020initialize(false);                // Initialize AD4020
  LTC2500initialize(LTC2500mode, false);  // Initialize LTC2500
  AD5791initialize(-10, 10);              // Initialize AD5791

  /******************************
   * Define interrupt routines for sampling of in- and outputs or for blinking LED */
  T4setInterrupt1(readADCs);                // Set the ISR (interrupt service routine) for ADC readout
  T4interSetup(GPT1, 1 / samplerate);       // Set the interval for the read interrupt
  if(!blinker) {
    T4setInterrupt2(writeDACs);             // Set the ISR for DAC output
    T4interSetup(GPT2, 1 / processingRate); // Set the interval for the output interrupt
  } else {
    T4setInterrupt2(blinking);              // Set the ISR for blinking LED
    T4interSetup(GPT2, 0.5);                // Set the interval for the blinking LED
  }

  /******************************
   * Add signals to the output or set PWM output */
  T4addSignal(1000.0, 1, 0);
  T4addSignal(1005.0, 1, 0);
  T4awV(DAC_TEENSY, 1.0);
//  AD5791setVoltage(1.0);


  /******************************
   * Finalise setup */
  T4addSerialFunc(checkUpdateUSB);   // Set the function to check the serial port for commands
  interrupts();                           // Setup complete, activate interrupts
}


/** @brief Main loop function
 */
void loop() {
  T4checkSerialBuffer();
  sendDataToPC();
  delay(1);
}


/** @brief Interrupt routine for writing values to the DACs
 */
void writeDACs() {
  if(!blinker) {T4dw(LED_2, HIGH);}
  AD5791setVoltage(T4sigValue());
  T4awV(DAC_TEENSY, T4sigValue() + 1.0);
  if(!blinker) {T4dw(LED_2, LOW);}
}


/** @brief Toggling the LED output state to indicate that the program is still running correctly
 */
void blinking() {
  T4toggle(LED_1);
}


/** @brief Interrupt routine for reading values from the ADCs and storing them in their respective data buffers.
 */
void readADCs() {
  if(full) {return;}  // The buffers are full, there is nothing to be read.
  if(!blinker) {T4dw(LED_1, HIGH);}
  int32_t val = 0;    // Variable to store the raw value of an ADC
  
  // Read the AD4020
  if(AD4020active) {
    val = AD4020readValue();            // Read value // 752 cycles
    sumAD4020 += val;
    //voltageAD4020 += RES_AD4020 * val;  // Convert raw value to voltage
  }
  
  // Read the LTC2500
  if(LTC2500active) {
    val = LTC2500readValue();             // Read value // 1325 cycles
    sumLTC2500 += val;
    //voltageLTC2500 += RES_LTC2500 * val;  // Convert raw value to voltage
  }
  
  // Read the internal ADC
  if(INTERNALADCactive) {
    val = T4ar(ADC_TEENSY); // Read value // 3388 cycles
    val -= 1 << 11;         // Shift value into the correct range
    sumInternal += val;
  }

  // The first value after sending data has to be disregarded since its time of recording is from the end of the last cycle
  if(sampleStart) {
    // Reset the sums
    sumAD4020 = 0;
    sumLTC2500 = 0;
    sumInternal = 0;
    sampleStart = false;
    if(!blinker) {T4dw(LED_1, LOW);}
    return;
  }

  samples++;  // Increment the number of samples taken
  
  // If the number of oversamples has been reached, check the trigger and possibly store the values
  if(samples >= oversamples) {
    // Average the samples
    sumAD4020 /= oversamples;
    sumLTC2500 /= oversamples;
    sumInternal /= oversamples;
    switch(signalType) {
      case signalVoltage: // Perform offset and gain correction
                          voltageAD4020 = RES_AD4020 * gainAD4020 * sumAD4020 + offsetAD4020;
                          voltageLTC2500 = RES_LTC2500 * gainLTC2500 * sumLTC2500 + offsetLTC2500;
                          voltageInternal = RES_Internal * gainInternal * sumInternal + offsetInternal;
                          break;
      case signalRaw:     voltageAD4020 = sumAD4020;
                          voltageLTC2500 = sumLTC2500;
                          voltageInternal = sumInternal;
                          break;
    }

    // Check the trigger conditions
    float triggerVoltage;
    switch(triggerSource) {
      case UNTRIGGERED: triggerState = TRIGGERED; // In this case the data is always being recorded
                        break;
      case AD4020:      triggerVoltage = voltageAD4020;
                        break;
      case LTC2500:     triggerVoltage = voltageLTC2500;
                        break;
      case INTERNALADC: triggerVoltage = voltageInternal;
                        break;
      case SCHMITT:     triggerVoltage = -10 + 20*T4dr(SCHMITT_TRIGGER);
                        
    }
    switch(triggerState) {
      case WAIT:      if((triggerFlank == RISE && triggerVoltage >= triggerThreshold) || (triggerFlank == FALL && triggerVoltage <= triggerThreshold)) {
                        triggerState = TRIGGERED;
                      }
                      break;
      case TRIGGERED: break;  // If the trigger is already active, there is nothing to be checked.
      case HOLDING:   if((triggerFlank == RISE && triggerVoltage <= triggerThreshold) || (triggerFlank == FALL && triggerVoltage >= triggerThreshold)) {
                        triggerState = WAIT;
                      }
    }
    if(triggerState != TRIGGERED) {
      // Reset the sums and samples
      sumAD4020 = 0;
      sumLTC2500 = 0;
      sumInternal = 0;
      samples = 0;
      if(!blinker) {T4dw(LED_1, LOW);}
      return;
    }
    
    // Store voltage value of the AD4020
    if(AD4020active) {
      bufAD4020[bufPos] = LBYTE(voltageAD4020);
      bufAD4020[bufPos+1] = HBYTE(voltageAD4020);
      bufAD4020[bufPos+2] = H2BYTE(voltageAD4020);
      bufAD4020[bufPos+3] = H3BYTE(voltageAD4020);
    }
  
    // Store voltage value of the LTC2500
    if(LTC2500active) {
      bufLTC2500[bufPos] = LBYTE(voltageLTC2500);
      bufLTC2500[bufPos+1] = HBYTE(voltageLTC2500);
      bufLTC2500[bufPos+2] = H2BYTE(voltageLTC2500);
      bufLTC2500[bufPos+3] = H3BYTE(voltageLTC2500);
    }
    
    // Store voltage value of the internal ADC
    if(INTERNALADCactive) {
      bufInternal[bufPos] = LBYTE(voltageInternal);
      bufInternal[bufPos+1] = HBYTE(voltageInternal);
      bufInternal[bufPos+2] = H2BYTE(voltageInternal);
      bufInternal[bufPos+3] = H3BYTE(voltageInternal);
    }
    
    // Reset the sums
    sumAD4020 = 0;
    sumLTC2500 = 0;
    sumInternal = 0;
    
    bufPos += 4;  // Increment the position in the data buffer
    samples = 0;  // Reset the number of samples
    // Check if the data buffers are full
    if(bufPos >= bufLen) {
      full = true;
      triggerState = HOLDING;
    }
  }
  if(!blinker) {T4dw(LED_1, LOW);}
}

/** @brief Sends buffers to PC once they are full
 */
void sendDataToPC() {
  if(!full) {return;} // If the buffers aren't full yet, there is nothing to be sent.
  bufPos = 0;
  sampleStart = true;
  // If the PC hasn't requested any data, it is discarded.
  if(!request) {
    full = false;
    return;
  }
  if(AD4020active)      {T4sw(bufAD4020, bufLen);}
  if(LTC2500active)     {T4sw(bufLTC2500, bufLen);}
  if(INTERNALADCactive) {T4sw(bufInternal, bufLen);}
  request = false;
  full = false;
}

/** @brief Processes commands received from the PC
 *
 *  @param command Command (in ASCII format) as received from PC
 *  @return false if an invalid command has been received. Otherwise true. 
 */
bool checkUpdateUSB(String command) {
  switch(checkCommand(command)) {
    case settingOversamples:    command.remove(0, 16);
                                oversamples = command.toInt();
                                return true;
                                break;
    case settingSize:           command.remove(0, 13);
                                bufLen = min(4*command.toInt(), maxLen);
                                return true;
                                break;
    case settingSpectralFreq:   command.remove(0, 15);
                                samplerate = max(1, command.toFloat());
                                T4interSetup(GPT1, 1 / samplerate);
                                return true;
                                break;
    case settingProcessingFreq: command.remove(0, 20);
                                processingRate = max(1, command.toFloat());
                                T4interSetup(GPT2, 1 / processingRate);
                                return true;
                                break;
    case settingTriggerSource:  command.remove(0, 18);
                                switch(checkTriggerSource(command)) {
                                  case UNTRIGGERED: triggerSource = UNTRIGGERED;
                                                    return true;
                                                    break;
                                  case AD4020:      triggerSource = AD4020;
                                                    return true;
                                                    break;
                                  case LTC2500:     triggerSource = LTC2500;
                                                    return true;
                                                    break;
                                  case INTERNALADC: triggerSource = INTERNALADC;
                                                    return true;
                                                    break;
                                  case SCHMITT:     triggerSource = SCHMITT;
                                                    return true;
                                                    break;
                                  case INVALID:     return false;
                                                    break;
                                }
                                return true;
                                break;
    case settingThreshold:      command.remove(0, 14);
                                triggerThreshold = command.toFloat();
                                return true;
                                break;
    case settingFlank:          command.remove(0, 10);
                                switch(checkFlank(command)) {
                                  case FALL:    triggerFlank = FALL;
                                                return true;
                                                break;
                                  case RISE:    triggerFlank = RISE;
                                                return true;
                                                break;
                                  case INVALID: return false;
                                                break;
                                }
                                break;
    case settingMode:       command.remove(0, 9);
                                switch(checkADC(command)) {
                                  case AD4020:      AD4020active = true;
                                                    return true;
                                                    break;
                                  case LTC2500:     LTC2500active = true;
                                                    return true;
                                                    break;
                                  case INTERNALADC: INTERNALADCactive = true;
                                                    return true;
                                                    break;
                                  case INVALID:     return false;
                                                    break;
                                }
                                break;
    case settingDeactivate:     command.remove(0, 11);
                                switch(checkADC(command)) {
                                  case AD4020:      AD4020active = false;
                                                    return true;
                                                    break;
                                  case LTC2500:     LTC2500active = false;
                                                    return true;
                                                    break;
                                  case INTERNALADC: INTERNALADCactive = false;
                                                    return true;
                                                    break;
                                  case INVALID:     return false;
                                                    break;
                                }
                                break;
    case settingSignalType:     command.remove(0, 15);
                                switch(checkSignalType(command)) {
                                  case signalVoltage: signalType = signalVoltage;
                                                      return true;
                                                      break;
                                  case signalRaw:     signalType = signalRaw;
                                                      return true;
                                                      break;
                                  case INVALID:       return false;
                                                      break;
                                }
                                break;
    case commandRequest:        request = true;
                                return true;
                                break;
    case INVALID:               return false;
                                break;
  }
  return false;
}


/** @brief Maps the ASCII commands to IDs.
 *
 *  Currently implemented are the maps:
 *
 *  set oversamples       ->  settingOversamples
 *  set dataSize          ->  settingSize
 *  set samplerate        ->  settingSpectralFreq
 *  set processing rate   ->  settingProcessingFreq
 *  set triggerSource     ->  settingTriggerSource
 *  set threshold         ->  settingThreshold
 *  set flank             ->  settingFlank
 *  activate              ->  settingMode
 *  deactivate            ->  settingDeactivate
 *  set signalType        ->  settingSignalType
 *  send data             ->  commandRequest
 *
 *  @param command Command (in ASCII format) as received from PC
 *  @return numerical identifier for the respective command.
 */
int checkCommand(String command) {
  if(command.startsWith("set oversamples "))      {return settingOversamples;}
  if(command.startsWith("set dataSize "))         {return settingSize;}
  if(command.startsWith("set samplerate "))       {return settingSpectralFreq;}
  if(command.startsWith("set processing rate "))  {return settingProcessingFreq;}
  if(command.startsWith("set triggerSource "))    {return settingTriggerSource;}
  if(command.startsWith("set threshold "))        {return settingThreshold;}
  if(command.startsWith("set flank "))            {return settingFlank;}
  if(command.startsWith("set mode "))             {return settingMode;}
  if(command.startsWith("deactivate "))           {return settingDeactivate;}
  if(command.startsWith("set signalType "))       {return settingSignalType;}
  if(command.startsWith("send data"))             {return commandRequest;}
  return INVALID;
}


/** @brief Maps the ASCII commands for trigger sources to IDs.
 *
 *  Currently implemented are the maps:
 *
 *  Untriggered (roll)  ->  UNTRIGGERED
 *  AD4020              ->  AD4020
 *  LTC2500             ->  LTC2500
 *  Internal ADC        ->  INTERNALADC
 *  Schmitt trigger     ->  SCHMITT
 *
 *  @param command Trigger source names (in ASCII format) as received from PC
 *  @return numerical identifier for the respective trigger source.
 */
int checkTriggerSource(String command) {
  if(command.startsWith("Untriggered (roll)"))  {return UNTRIGGERED;}
  if(command.startsWith("AD4020"))              {return AD4020;}
  if(command.startsWith("LTC2500"))             {return LTC2500;}
  if(command.startsWith("Internal ADC"))        {return INTERNALADC;}
  if(command.startsWith("Schmitt trigger"))     {return SCHMITT;}
  return INVALID;
}

/** @brief Maps the ASCII command for trigger edge to IDs.
 *
 *  Currently implemented are the maps:
 *
 *  Falling ->  FALL
 *  Rising  ->  RISE
 *
 *  @param command Trigger edge names (in ASCII format) as received from PC
 *  @return numerical identifier for the respective trigger edge.
 */
int checkFlank(String command) {
  if(command.startsWith("Falling")) {return FALL;}
  if(command.startsWith("Rising"))  {return RISE;}
  return INVALID;
}

/** @brief Maps the ASCII command for ADCs to IDs.
 *
 *  Currently implemented are the maps:
 *
 *  AD4020              ->  AD4020
 *  LTC2500             ->  LTC2500
 *  Internal ADC        ->  INTERNALADC
 *
 *  @param command ADC names (in ASCII format) as received from PC
 *  @return numerical identifier for the respective ADC.
 */
int checkADC(String command) {
  if(command.startsWith("AD4020"))        {return AD4020;}
  if(command.startsWith("LTC2500"))       {return LTC2500;}
  if(command.startsWith("Internal ADC"))  {return INTERNALADC;}
  return INVALID;
}

/** @brief Maps the ASCII command for signal types to IDs.
 *
 *  Currently implemented are the maps:
 *
 *  voltage ->  signalVoltage
 *  raw     ->  signalRaw
 *
 *  @param command Signal type names (in ASCII format) as received from PC
 *  @return numerical identifier for the respective signal type.
 */
int checkSignalType(String command) {
  if(command.startsWith("voltage")) {return signalVoltage;}
  if(command.startsWith("raw"))     {return signalRaw;}
  return INVALID;
}
