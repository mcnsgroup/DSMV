/** @file SpectralProcessingDSMV.ino
 *  @brief Reads the data from the LTC2500, processes it, and writes the result to the AD5791. Input of AD4020 is used for spectral analysis.
 *
 *  Requires a Teensy 4.0 together with DSMV Board version 2.0
 *  Use together with the Python scripts SpectralProcessing.py and 
 *  SpectralProcessingGUI.py.
 *  
 *  @author Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
 *  @author Philipp Rahe (prahe@uos.de)
 *  @date 28.06.2022
 *  @version 1.9
 *  
 *  @par Changelog
 *  - 28.06.2022: Fixed a bug that caused the IIR-Filter to not use the most recent values correctly
 *  - 27.06.2022: Changed arithmetic to the format of a filter property
 *  - 21.06.2022: Fixed a bug that caused the updated arithmetic to only be applied to the current filter,
 *                added functionality to configure all different arithmetics via USB command
 *  - 17.06.2022: Added functionality to configure FIR filter arithmetic via USB command,
 *                significantly improved the performance of FIR filters,
 *                moved all filters to external files
 *  - 08.06.2022: Fixed a bug that caused the FIR filter to not be recalculated on a property update
 *  - 07.06.2022: Changed maximum cycle length for impulse response mode to match maximum data size even for step response,
 *                added option to configure filter window via USB protocol,
 *                fixed a bug that caused the filter properties to not be updated properly for FIR filters
 *  - 03.06.2022: Changed spectral reading to occur in tandem with filter processing
 *                while not in spectral operation mode
 *  - 02.06.2022: Fixed a bug that caused the one-parameter filters to not work properly after a property update,
 *                merged features with ImpulseProcessingDSMV
 *  - 31.05.2022: Added functionality to configure filters via USB protocol,
 *                moved different filters to individual files,
 *  - 23.05.2022: Added command for sending data to PC to USB protocol,
 *                changed averaging to integer arithmetic,
 *                added functionality to send raw values to the PC (controlled via USB command),
 *                fixed a bug that caused the LTC2500 to apply the oversamples of AD4020
 *  - 26.01.2022: Decreased interval between processing received commands
 *  - 21.01.2022: Documentation translated to English
 *  - 08.06.2021: Added moving average, high pass and low pass filters
 *  - 05.06.2021: initial version
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

float offsetAD4020 = 0;   /**< Offset voltage for the AD4020. */
float gainAD4020 = 1.0;   /**< Gain factor for the AD4020. */
float offsetLTC2500 = 0;  /**< Offset voltage for the LTC2500. */
float gainLTC2500 = 1.0;  /**< Gain factor for the LTC2500. */

bool blinker = false; /**< Specifies usage of LED_1. true: 1s interval (Note: This deactivates the analog output!). false: loop duration. */

#define RES_AD4020  0.0000190734863 /**< Resolution of the AD4020. */
#define RES_LTC2500 0.0000011920929 /**< Resolution of the LTC2500. */
#define LTC2500mode noLatencyOutput /**< Specifies the output mode of the LTC2500. */
#define INVALID -1                  /**< Invalid command. */
#define settingMode 0               /**< Setting for the mode of operation. */
#define settingOversamples 1        /**< Setting for the number of oversamples: */
#define settingSize 2               /**< Setting for the data size. */
#define settingSpectralFreq 3       /**< Setting for the sampling frequency. */
#define settingProcessingFreq 4     /**< Setting for the reading, processing and output frequency. */
#define settingSignalType 5         /**< Setting for the signal type sent to the PC. */
#define settingFilter 6             /**< Setting for the filter type. */
#define settingFilterProperty1 7    /**< Setting for the (1st) filter porperty. */
#define settingFilterProperty2 8    /**< Setting for the 2nd filter porperty. */
#define settingFilterProperty3 9    /**< Setting for the 3rd filter porperty. */
#define settingFilterProperty4 10   /**< Setting for the 4rd filter porperty. */
#define settingFilterProperty5 11        /**< Setting for the arithmetic used by the filters. */
#define commandRequest 12           /**< Command for requesting data to be sent to the PC. */
#define signalVoltage 0             /**< Voltage read from ADCs. */
#define signalRaw 1                 /**< Raw value read from ADCs. */

#define spectral 0    /**< Spectral analysis of AD4020 and signal processing (base functionality). */
#define shortPulse 1  /**< Short on-off pulse and base functionality. */
#define turnOn 2      /**< Long turn on pulse and base functionality. */
#define turnOff 3     /**< Long turn off pulse and base functionality. */
int mode = spectral;  /**< Operation mode. */

#define defaultSamplerate 20000     /**< Default value for sampling frequency for specral analysis. */
#define defaultProcessingRate 5000  /**< Default value for frequency for reading the LTC2500, processing the data and output at the AD5791. */

const int numFilters = 12;  /**< Number of filters. */
const int numProps = 6;     /**< Number of properties per filter. */

// Different filters and their default properties
#define scaling 0
#define defaultScaling {1, NULL, NULL, NULL, NULL, NULL}
#define movingAvg 1
#define defaultMovingAvg {1, NULL, NULL, NULL, NULL, NULL}
#define lpf1 2
#define defaultLpf1 {0, NULL, NULL, NULL, NULL, defaultProcessingRate}
#define hpf1 3
#define defaultHpf1 {0, NULL, NULL, NULL, NULL, defaultProcessingRate}
#define bandpass 4
#define defaultBandpass {0, 0, 1, rectWin, integerDoubleBuffer, defaultProcessingRate}
#define bandstop 5
#define defaultBandstop {0, 0, 1, rectWin, integerDoubleBuffer, defaultProcessingRate}
#define FIRlow 6
#define defaultFIRlow {0, NULL, 1, rectWin, integerDoubleBuffer, defaultProcessingRate}
#define FIRhigh 7
#define defaultFIRhigh {0, NULL, 1, rectWin, integerDoubleBuffer, defaultProcessingRate}
#define lpf2 8
#define defaultLpf2 {0, NULL, NULL, NULL, NULL, defaultProcessingRate}
#define lpf3 9
#define defaultLpf3 {0, NULL, NULL, NULL, NULL, defaultProcessingRate}
#define progIIR 10
#define defaultProgIIR {NULL, NULL, NULL, NULL, NULL, NULL}
#define ownDef 11
#define defaultOwnDef {NULL, NULL, NULL, NULL, NULL, NULL}

// Include filter functions
#include "scale.h"
#include "avg.h"
#include "lpf1.h"
#include "hpf1.h"
#include "fir.h"
#include "lpf2.h"
#include "lpf3.h"
#include "iir.h"
#include "ownDef.h"

/** Array holding the properties of all filters.
 *  
 *  Note that integer values can't be bigger than 16777216 in this format due to float inaccuracy.
 */
float filterProperties[numFilters][numProps] = {
  defaultScaling,
  defaultMovingAvg,
  defaultLpf1,
  defaultHpf1,
  defaultBandpass,
  defaultBandstop,
  defaultFIRlow,
  defaultFIRhigh,
  defaultLpf2,
  defaultLpf3,
  defaultProgIIR,
  defaultOwnDef
};

int filter = progIIR;   /**< Currently selected filter. */
float scalingGain = 1;  /**< Scaling gain for all filters. */

const uint32_t maxLen = 4*32768;              /**< Maximum length of the data buffers in bytes. */
uint32_t bufLen = 4*100;                      /**< Current length of the data buffers in bytes. */
uint8_t bufAD4020[maxLen];                    /**< Data buffer for the AD4020. */
uint8_t bufLTC2500[maxLen];                   /**< Data buffer for the LTC2500. */
int32_t bufPos = 0;                           /**< Position in the data buffers to write to. */
bool full = false;                            /**< Specifies whether or not the buffer is ready to be sent to the PC. */
bool request = false;                         /**< Specifies whether or not the PC has requested data to be sent. */
bool wait = true;                             /**< Specifies whether the AD4020 is waiting for the pulse. */
int ADready = 0;                              /**< Specifies whether the AD4020 is ready for the pulse: 
                                                   0=discard one sample, 1=read first data point, 2=discard another sample,
                                                   3=continuous read*/
bool sampleStart = true;                      /**< Specifies whether or not the sampling for the next data set has just begun. */
float samplerate = defaultSamplerate;         /**< Sampling frequency for specral analysis. */
float processingRate = defaultProcessingRate; /**< Frequency for reading the LTC2500, processing the data and output at the AD5791. */
int oversamples = 1;                          /**< Number of oversamples (for spectral analysis). */
int samples = 0;                              /**< Number of samples since last storing (for spectral analysis). */
int signalType = signalVoltage;               /**< Signal type sent to the PC. */
float voltageAD4020 = 0;                      /**< Stores the current voltage value of the AD4020 */
int64_t sumAD4020 = 0;                        /**< Stores the current sum of the raw values of the AD4020. */
float voltageLTC2500 = 0;                     /**< Stores the current voltage value of the LTC2500 */

/** @brief initialises the sketch
 */
void setup() {
  noInterrupts();                         // Prevent interrupts from triggering during setup
  setOutputPins();                        // Configure pins of the board
  T4dw(MOSI_ADC, HIGH);                   // Set the MOSI of the ADCs to HIGH
  T4TimerInit();                          // Initialize timer counter
  AD4020initialize(false);                // Initialize AD4020
  LTC2500initialize(LTC2500mode, false);  // Initialize LTC2500
  AD5791initialize(-10, 10);              // Initialize AD5791
  /******************************
   * Define interrupt routines for sampling of in- and outputs */
  T4setInterrupt1(readProcessOutput);     // Set the ISR (interrupt service routine) for ADC reading, processing and output of the signal
  T4interSetup(GPT1, 1 / processingRate); // Set the interval for the read interrupt
  T4setInterrupt2(spectralRead);          // Set the ISR for specral reading
  T4interSetup(GPT2, 1 / samplerate);     // Set the interval for the output interrupt

  /*****************************
   * Set default filter to ownDef (Exercise 8.B)
   */
  filter = ownDef;

  /******************************
   * Finalise setup */
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

/** @brief Interrupt routine for spectral reading
 */
void spectralRead() {
  if(full) {return;}               // The buffer is full, there is nothing to be read.
  int32_t val = AD4020readValue(); // Read the raw value of the AD4020
  
  // Don't store the value to the buffer if it isn't valid yet in case of pulse or step response
  if(mode != spectral) {
    if(ADready == 0) {
      ADready = 1;
      return;
    } else if(ADready == 2 && !wait) {
      ADready = 3;
      return;
    }
  }
  
  sumAD4020 += val;//voltageAD4020 += RES_AD4020 * val;  // Convert it into a voltage
  
  // The first value after sending data has to be disregarded since its time of recording is from the end of the last cycle
  if(sampleStart) {
    // Reset the sum
    sumAD4020 = 0;
    //voltageAD4020 = 0;
    sampleStart = false;
    return;
  }

  samples++;  // Increment the number of samples taken
  
  // If the number of oversamples has been reached, store the values
  if(samples >= oversamples) {
    // Sufficient samples read for a value, cycle can begin
    if(mode != spectral && ADready == 1) {
      ADready = 2;
    }
    // Average the samples
    sumAD4020 /= oversamples;
    switch(signalType) {
      case signalVoltage: // Perform offset and gain correction
                          voltageAD4020 = RES_AD4020 * gainAD4020 * sumAD4020 + offsetAD4020;
                          break;
      case signalRaw:     voltageAD4020 = sumAD4020;
                          break;
    }
    //voltageAD4020 = voltageAD4020 / oversamples * gainAD4020 + offsetAD4020;
    
    // Store voltage value of the AD4020
    bufAD4020[bufPos] = LBYTE(voltageAD4020);
    bufAD4020[bufPos+1] = HBYTE(voltageAD4020);
    bufAD4020[bufPos+2] = H2BYTE(voltageAD4020);
    bufAD4020[bufPos+3] = H3BYTE(voltageAD4020);
    
    // Reset the sum
    sumAD4020 = 0;
    // Only advance the buffer position if the cycle is underway
    if(mode == spectral || !wait) {
      // Increment the position in the data buffer
      bufPos += 4;
    }
    // Reset the number of samples
    samples = 0;
    // Check if the data buffers are full
    if(bufPos >= bufLen) {
      full = true;
      wait = true;
    }
  }
}


/** @brief Toggling the LED_1 to indicate that the program is still running correctly
 */
void blinking() {
  T4toggle(LED_1);
}


int nproc = 0;
int nmax = bufLen / 2;

/** @brief Interrupt routine for ADC reading, processing, and signal output
 */
void readProcessOutput() {
  //T4toggle(LED_3);
  // Possibly read
  if(mode != spectral) {
    spectralRead();
  }
  // Read the raw value of the LTC2500
  int32_t val = LTC2500readValue();

  // Convert it into a voltage
  voltageLTC2500 = RES_LTC2500 * val; 
  
  // Offset/gain correction
  voltageLTC2500 = voltageLTC2500 * gainLTC2500 + offsetLTC2500;
  
  // Output value: pass-through
  float outputValue = voltageLTC2500;
  
  // Trigger timing LED to measure filter performance
  //T4toggle(LED_3);
  /***** Processing of input data */
  switch(filter) {
    case scaling:   outputValue = proc_scale(outputValue, filterProperties[filter]);
                    break;
    case movingAvg: outputValue = proc_avg(outputValue, filterProperties[filter]);
                    break;
    case lpf1:      outputValue = proc_lpf1(outputValue, filterProperties[filter]);
                    break;
    case hpf1:      outputValue = proc_hpf1(outputValue, filterProperties[filter]);
                    break;
    case bandpass:  outputValue = proc_fir(outputValue, val, filterProperties[filter]);
                    break;
    case bandstop:  outputValue = proc_fir(outputValue, val, filterProperties[filter]);
                    break;
    case FIRlow:    outputValue = proc_fir(outputValue, val, filterProperties[filter]);
                    break;
    case FIRhigh:   outputValue = proc_fir(outputValue, val, filterProperties[filter]);
                    break;
    case lpf2:      outputValue = proc_lpf2(outputValue, filterProperties[filter]);
                    break;
    case lpf3:      outputValue = proc_lpf3(outputValue, filterProperties[filter]);
                    break;
    case progIIR:   outputValue = proc_iir(outputValue, filterProperties[filter]);
                    break;
    case ownDef:    outputValue = proc_ownDef(outputValue, filterProperties[filter]);
                    break;
  }
  //T4toggle(LED_3);

  // Apply scaling gain if not done already
  if(filter != scaling) {outputValue *= scalingGain;}
  
  // Output the result on the AD5791
  AD5791setVoltage(outputValue);
  
  // Possibly send configured
  if(ADready >= 2) {
    if(nproc==0) {
      switch(mode) {
        case shortPulse:  T4dw(DAC_TEENSY, HIGH);
                          wait = false;
                          break;
        case turnOn:      T4dw(DAC_TEENSY, HIGH);
                          wait = false;
                          break;
        case turnOff:     T4dw(DAC_TEENSY, LOW);
                          wait = false;
                          break;
      }
    } else if(nproc==1 && mode == shortPulse) {
      T4dw(DAC_TEENSY, LOW);
    } else if(nproc >= nmax / 2){
      switch(mode) {
        case shortPulse:  break;
        case turnOn:      T4dw(DAC_TEENSY, LOW);
                          break;
        case turnOff:     T4dw(DAC_TEENSY, HIGH);
                          break;
      }
    }
    nproc++;
    if(nproc >= nmax) {
      nproc = 0;
      wait = true;
    }
  }
  //T4toggle(LED_3);
}

/** @brief Resets the history values for the high- and low-pass filter.
 *  
 */
void resetHistory() {
  yln_1 = 0.0;
  xhn_1 = 0.0;
  yhn_1 = 0.0;
  yl2n_1 = 0.0;
  yl2n_2 = 0.0;
  yl3n_1 = 0.0;
  yl3n_2 = 0.0;
  yl3n_3 = 0.0;
  for(int i = 0; i < sizeof(ynhist)/sizeof(ynhist[0]); i++) {
    ynhist[i] = 0;
    xnhist[i] = 0;
  }
}

/** @brief Sends buffers to PC once they are full
 */
void sendDataToPC() {
  if(!full) {return;} // If the buffers aren't full yet, there is nothing to be sent.
  bufPos = 0;
  sampleStart = true;
  // If the PC hasn't requested any data, it is discarded.
  if(!request) {
    wait = true;
    full = false;
    ADready = 0;
    return;
  }
  T4sw(bufAD4020, bufLen);
  request = false;
  wait = true;
  full = false;
  ADready = 0;
}

/** @brief Processes commands received from the PC
 *
 *  @param command Command (in ASCII format) as received from PC
 *  @return false if an invalid command has been received. Otherwise true. 
 */
bool checkUpdateUSB(String command) {
  switch(checkCommand(command)) {
    case settingMode:           command.remove(0, 9);
                                switch(checkMode(command)) {
                                  case spectral:    mode = spectral;
                                                    T4setInterrupt2(spectralRead);
                                                    return true;
                                                    break;
                                  case shortPulse:  mode = shortPulse;
                                                    samplerate = processingRate;
                                                    T4setInterrupt2(T4foo);
                                                    return true;
                                                    break;
                                  case turnOn:      mode = turnOn;
                                                    samplerate = processingRate;
                                                    T4setInterrupt2(T4foo);
                                                    return true;
                                                    break;
                                  case turnOff:     mode = turnOff;
                                                    samplerate = processingRate;
                                                    T4setInterrupt2(T4foo);
                                                    return true;
                                                    break;
                                  case INVALID:     return false;
                                                    break;
                                }
                                break;
    case settingOversamples:    command.remove(0, 16);
                                oversamples = command.toInt();
                                return true;
                                break;
    case settingSize:           command.remove(0, 13);
                                bufLen = min(4*command.toInt(), maxLen);
                                nmax = bufLen / 2;
                                return true;
                                break;
    case settingSpectralFreq:   command.remove(0, 15);
                                samplerate = max(1, command.toFloat());
                                T4interSetup(GPT2, 1 / samplerate);
                                return true;
                                break;
    case settingProcessingFreq: command.remove(0, 20);
                                processingRate = max(1, command.toFloat());
                                T4interSetup(GPT1, 1 / processingRate);
                                for(int i=0; i < numFilters; i++) {
                                  filterProperties[i][5] = processingRate;
                                }
                                init_fir(filter, filterProperties[filter]);
                                return true;
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
    case settingFilter:         command.remove(0, 11);
                                switch(checkFilter(command)) {
                                  case scaling:   filter = scaling;
                                                  return true;
                                                  break;
                                  case movingAvg: filter = movingAvg;
                                                  return true;
                                                  break;
                                  case lpf1:      filter = lpf1;
                                                  resetHistory();
                                                  return true;
                                                  break;
                                  case hpf1:      filter = hpf1;
                                                  resetHistory();
                                                  return true;
                                                  break;
                                  case bandpass:  filter = bandpass;
                                                  init_fir(filter, filterProperties[filter]);
                                                  return true;
                                                  break;
                                  case bandstop:  filter = bandstop;
                                                  init_fir(filter, filterProperties[filter]);
                                                  return true;
                                                  break;
                                  case FIRlow:    filter = FIRlow;
                                                  init_fir(filter, filterProperties[filter]);
                                                  return true;
                                                  break;
                                  case FIRhigh:   filter = FIRhigh;
                                                  init_fir(filter, filterProperties[filter]);
                                                  return true;
                                                  break;
                                  case lpf2:      filter = lpf2;
                                                  resetHistory();
                                                  return true;
                                                  break;
                                  case lpf3:      filter = lpf3;
                                                  resetHistory();
                                                  return true;
                                                  break;
                                  case progIIR:   filter = progIIR;
                                                  resetHistory();
                                                  return true;
                                                  break;
                                  case ownDef:   filter = ownDef;
                                                  resetHistory();
                                                  return true;
                                                  break;
                                }
                                break;
    case settingFilterProperty1:command.remove(0, 20);
                                filterProperties[filter][0] = command.toFloat();
                                resetHistory();
                                if(filter == scaling) {scalingGain = filterProperties[filter][0];}
                                switch(filter) {
                                  case bandpass:  init_fir(filter, filterProperties[filter]);
                                                  return true;
                                                  break;
                                  case bandstop:  init_fir(filter, filterProperties[filter]);
                                                  return true;
                                                  break;
                                  case FIRlow:    init_fir(filter, filterProperties[filter]);
                                                  return true;
                                                  break;
                                  case FIRhigh:   init_fir(filter, filterProperties[filter]);
                                                  return true;
                                                  break;
                                }
                                break;
    case settingFilterProperty2:command.remove(0, 20);
                                filterProperties[filter][1] = command.toFloat();
                                switch(filter) {
                                  case bandpass:  init_fir(filter, filterProperties[filter]);
                                                  return true;
                                                  break;
                                  case bandstop:  init_fir(filter, filterProperties[filter]);
                                                  return true;
                                                  break;
                                  case FIRlow:    init_fir(filter, filterProperties[filter]);
                                                  return true;
                                                  break;
                                  case FIRhigh:   init_fir(filter, filterProperties[filter]);
                                                  return true;
                                                  break;
                                }
                                break;
    case settingFilterProperty3:{
                                  command.remove(0, 20);
                                  uint16_t Mfilter = min(max(command.toInt(), 0) / 2, MfilterMax);
                                  uint16_t Nfilter = 2*Mfilter + 1;
                                  filterProperties[filter][2] = Nfilter;
                                  switch(filter) {
                                    case bandpass:  init_fir(filter, filterProperties[filter]);
                                                    return true;
                                                    break;
                                    case bandstop:  init_fir(filter, filterProperties[filter]);
                                                    return true;
                                                    break;
                                    case FIRlow:    init_fir(filter, filterProperties[filter]);
                                                    return true;
                                                    break;
                                    case FIRhigh:   init_fir(filter, filterProperties[filter]);
                                                    return true;
                                                    break;
                                  }
                                  return true;
                                  break;
                                }
    case settingFilterProperty4:command.remove(0, 20);
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
    case settingFilterProperty5:command.remove(0, 20);
                                switch(checkArithmetic(command)) {
                                  case integerDoubleBuffer: filterProperties[filter][4] = integerDoubleBuffer;
                                                            return true;
                                                            break;
                                  case integerIfModulo:     filterProperties[filter][4] = integerIfModulo;
                                                            return true;
                                                            break;
                                  case integerModulo:       filterProperties[filter][4] = integerModulo;
                                                            return true;
                                                            break;
                                  case floatDoubleBuffer:   filterProperties[filter][4] = floatDoubleBuffer;
                                                            return true;
                                                            break;
                                  case floatIfModulo:       filterProperties[filter][4] = floatIfModulo;
                                                            return true;
                                                            break;
                                  case floatModulo:         filterProperties[filter][4] = floatModulo;
                                                            return true;
                                                            break;
                                  case INVALID:             return false;
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
 *  set signalType        ->  settingSignalType
 *  set filter            ->  settingFilter
 *  set filterProperty1   ->  settingFilterProperty1
 *  set filterProperty2   ->  settingFilterProperty2
 *  set filterProperty3   ->  settingFilterProperty3
 *  set filterProperty4   ->  settingFilterProperty4
 *  set filterProperty5   ->  settingFilterProperty5
 *  send data             ->  commandRequest
 *
 *  @param command Command (in ASCII format) as received from PC
 *  @return numerical identifier for the respective command.  
 */
int checkCommand(String command) {
  if(command.startsWith("set mode "))             {return settingMode;}
  if(command.startsWith("set oversamples "))      {return settingOversamples;}
  if(command.startsWith("set dataSize "))         {return settingSize;}
  if(command.startsWith("set samplerate "))       {return settingSpectralFreq;}
  if(command.startsWith("set processing rate "))  {return settingProcessingFreq;}
  if(command.startsWith("set signalType "))       {return settingSignalType;}
  if(command.startsWith("set filter "))           {return settingFilter;}
  if(command.startsWith("set filterProperty1 "))  {return settingFilterProperty1;}
  if(command.startsWith("set filterProperty2 "))  {return settingFilterProperty2;}
  if(command.startsWith("set filterProperty3 "))  {return settingFilterProperty3;}
  if(command.startsWith("set filterProperty4 "))  {return settingFilterProperty4;}
  if(command.startsWith("set filterProperty5 "))  {return settingFilterProperty5;}
  if(command.startsWith("send data"))             {return commandRequest;}
  return INVALID;
}

/** @brief Maps the ASCII commands to operation mode IDs.
 *
 *  Currently implemented are the maps:
 *  
 *  AD4020 spectral analysis                -> spectral
 *  Pulse response & signal processing      -> shortPulse
 *  Step up response & signal processing    ->  turnOn
 *  Step down response & signal processing  ->  turnOff
 *
 *  @param command Command (in ASCII format) as received from PC
 *  @return numerical identifier for the respective filter.  
 */
int checkMode(String command) {
  if(command.startsWith("AD4020 spectral analysis"))                {return spectral;}
  if(command.startsWith("Pulse response & signal processing"))      {return shortPulse;}
  if(command.startsWith("Step up response & signal processing"))    {return turnOn;}
  if(command.startsWith("Step down response & signal processing"))  {return turnOff;}
  return INVALID;
}

/** @brief Maps the ASCII commands to filter IDs.
 *
 *  Currently implemented are the maps:
 *
 *  Scaling                     ->  scaling
 *  Moving average              ->  movingAvg
 *  Low pass filter 1st prder   ->  lpf1
 *  High pass filter 1st order  ->  hpf1
 *  FIR bandpass filter         ->  bandpass
 *  FIR bandstop filter         ->  bandstop
 *  FIR low pass filter         ->  FIRlow
 *  FIR high pass filter        ->  FIRhigh
 *  Low pass filter 2nd order   ->  lpf2
 *  Low pass filter 3rd order   ->  lpf3
 *  Programmable IIR filter     ->  progIIR
 *
 *  @param command Command (in ASCII format) as received from PC
 *  @return numerical identifier for the respective filter.  
 */
int checkFilter(String command) {
  if(command.startsWith("Scaling"))                   {return scaling;}
  if(command.startsWith("Moving average"))            {return movingAvg;}
  if(command.startsWith("Low pass filter 1st order")) {return lpf1;}
  if(command.startsWith("High pass filter 1st order")){return hpf1;}
  if(command.startsWith("FIR bandpass filter"))       {return bandpass;}
  if(command.startsWith("FIR bandstop filter"))       {return bandstop;}
  if(command.startsWith("FIR low pass filter"))       {return FIRlow;}
  if(command.startsWith("FIR high pass filter"))      {return FIRhigh;}
  if(command.startsWith("Low pass filter 2nd order")) {return lpf2;}
  if(command.startsWith("Low pass filter 3rd order")) {return lpf3;}
  if(command.startsWith("Programmable IIR filter"))   {return progIIR;}
  if(command.startsWith("Own definition"))            {return ownDef;}
  T4pln(command);
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
