/** @file SpectralProcessingDSMV.ino
 *  @brief Reads the data from the LTC2500, processes it, and writes the result to the AD5791. Input of AD4020 is used for spectral analysis.
 *
 *  Requires a Teensy 4.0 together with DSMV Board version 2.0
 *  Use together with the Python scripts SpectralProcessing.py and 
 *  SpectralProcessingGUI.py.
 *  
 *  @author Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
 *  @author Philipp Rahe (prahe@uos.de)
 *  @date 23.05.2022
 *  @version 1.3
 *  
 *  @par Changelog
 *  - 23.05.2022: Added command for sending data to PC to USB protocol,
 *                changed averaging to integer arithmetic,
 *                added functionality to send raw values to the PC (controlled via USB command),
 *                fixed a bug that caused the LTC2500 to apply the oversamples of AD4020
 *  - 26.01.2022: Decreased interval between processing received commands
 *  - 21.01.2022: Documentation fully translated to English
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

float offsetAD4020 = 0;         /**< Offset voltage for the AD4020. */
float gainAD4020 = 1.0;         /**< Gain factor for the AD4020. */
float offsetLTC2500 = 0;        /**< Offset voltage for the LTC2500. */
float gainLTC2500 = 1.0;        /**< Gain factor for the LTC2500. */

bool blinker = false;           /**< Specifies usage of LED_1. true: 1s interval (Note: This deactivates the analog output!). false: loop duration. */


#define RES_AD4020  0.0000190734863 /**< Resolution of the AD4020. */
#define RES_LTC2500 0.0000011920929 /**< Resolution of the LTC2500. */
#define LTC2500mode noLatencyOutput /**< Specifies the output mode of the LTC2500. */
#define settingOversamples 0        /**< Setting for the number of oversamples: */
#define settingSize 1               /**< Setting for the data size. */
#define settingSpectralFreq 2       /**< Setting for the sampling frequency. */
#define settingProcessingFreq 3     /**< Setting for the reading, processing and output frequency. */
#define settingSignalType 4         /**< Setting for the signal type sent to the PC. */
#define commandRequest 5            /**< Command for requesting data to be sent to the PC. */
#define signalVoltage 0             /**< Voltage read from ADCs. */
#define signalRaw 1                 /**< Raw value read from ADCs. */
#define INVALID -1                  /**< Invalid command. */


const uint32_t maxLen = 4*32768;  /**< Maximum length of the data buffers in bytes. */
uint32_t bufLen = 4*100;          /**< Current length of the data buffers in bytes. */
uint8_t bufAD4020[maxLen];        /**< Data buffer for the AD4020. */
uint8_t bufLTC2500[maxLen];       /**< Data buffer for the LTC2500. */
int32_t bufPos = 0;               /**< Position in the data buffers to write to. */
bool full = false;                /**< Specifies whether or not the buffer is ready to be sent to the PC. */
bool request = false;             /**< Specifies whether or not the PC has requested data to be sent. */
bool sampleStart = true;          /**< Specifies whether or not the sampling for the next data set has just begun. */
float samplerate = 20000;         /**< Sampling frequency for specral analysis. */
float processingRate = 5000;      /**< Frequency for reading the LTC2500, processing the data and output at the AD5791. */
int oversamples = 1;              /**< Number of oversamples (for spectral analysis). */
int samples = 0;                  /**< Number of samples since last storing (for spectral analysis). */
int signalType = signalVoltage;   /**< Signal type sent to the PC. */
float voltageAD4020 = 0;          /**< Stores the current voltage value of the AD4020 */
int64_t sumAD4020 = 0;            /**< Stores the current sum of the raw values of the AD4020. */
float voltageLTC2500 = 0;         /**< Stores the current voltage value of the LTC2500 */


/** @brief initialises the sketch
 */
void setup() {
  noInterrupts();                         // Prevent interrupts from triggering during setup
  setOutputPins();                        // Configure pins of the board
  digitalWrite(MOSI_ADC, HIGH);           // Set the MOSI of the ADCs to HIGH
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

  /******************************
   * Finalise setup */
  T4addSerialFunc(checkUpdateUSB);   // Set the function to check the serial port for commands
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
    
    sumAD4020 = 0;//voltageAD4020 = 0;  // Reset the sum
    bufPos += 4;        // Increment the position in the data buffer
    samples = 0;        // Reset the number of samples
    // Check if the data buffers are full
    if(bufPos >= bufLen) {
      full = true;
    }
  }
}


/** @brief Toggling the LED output state to indicate that the program is still running correctly
 */
void blinking() {
  T4toggle(LED_1);
}


/** @brief Interrupt routine for ADC reading, processing, and signal output
 */
void readProcessOutput() {
  T4toggle(LED_3);
  // Read the raw value of the LTC2500
  int32_t val = LTC2500readValue();

  // Convert it into a voltage
  voltageLTC2500 = RES_LTC2500 * val; 
  
  // Offset/gain correction
  voltageLTC2500 = voltageLTC2500 * gainLTC2500 + offsetLTC2500;
  
  // Output value: pass-through
  float outputValue = voltageLTC2500;

  /***** Processing of input data */
  /* Amplification/attenuation */
  //outputValue = proc_scale(voltageLTC2500, 100.0);

  /* Moving averaging filter */
  //outputValue = proc_avg(outputValue, 10);

  /* Low-pass filter */
  //outputValue = proc_lpf(outputValue, 500);

  /* High-pass filter */
  //outputValue = proc_hpf(outputValue, 2000);

  // Output the result on the AD5791
  AD5791setVoltage(outputValue);
  T4toggle(LED_3);
}


/** @brief Amplifies or attenuates a signal by given factor 
 *  
 *  IO-equation: y_n = factor * x_n
 *  
 *  @param value analog input value
 *  @param factor amplification (factor>1.0) or attenuation (factor<1.0) factor
 *  @return Resulting signal value
 */
float proc_scale(float value, float factor) {
  return value*factor;
}

/* Ring buffer for moving average filter */
#define Nmax 256
float dbuffer[Nmax];
int idbuffer = 0;

/** @brief Moving averaging filter
 *  
 *  @param value last read value of the input signal
 *  @param samples number of samples to be averaged
 *  @return averaged value
 */
float proc_avg(float value, int samples) {

  // only Nmax averages at maximum allowed
  if(samples > Nmax) {
    samples = Nmax;
  }
  // need at least one sample
  if(samples <= 0 ) {
    samples = 1;
  }

  // store current value in buffer
  dbuffer[idbuffer] = value;

  // average the last <samples> values
  float avg = 0;
  for(int i=0; i<samples; i++) {
    if(idbuffer-i>=0) {
      avg += dbuffer[idbuffer-i];
    } else {
      avg += dbuffer[Nmax+(idbuffer-i)];
    }
  }
  avg/=samples;

  // advance pointer
  idbuffer++;
  if(idbuffer>=Nmax) {
    idbuffer = 0;
  }

  return avg;
}


/* history value for lpf */
float yln_1 = 0.0;

/** @brief Implements a low-pass filter
 *  
 *  @param xn value of the input signal to be filtered
 *  @param fc cutoff frequency
 *  @return filtered value
 */
float proc_lpf(float xn, float fc) {
  float fac = processingRate/(2.0*PI*fc);
  float out = 1.0/(fac+1.0)*(xn + fac*yln_1);
  yln_1 = out;
  return out;
  
}

/* history values for hpf */
float xhn_1 = 0.0;
float yhn_1 = 0.0;

/** @brief Implements a high-pass filter
 *  
 *  @param xn value of the input signal to be filtered
 *  @param fc cutoff frequency
 *  @return filtered value
 */
float proc_hpf(float xn, float fc) {
  float fac = (2.0*PI*fc)/processingRate;
  float out = 1.0/(fac+1.0)*(xn + yhn_1-xhn_1);
  yhn_1 = out;
  xhn_1 = xn;
  return out;
  
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
  T4sw(bufAD4020, bufLen);
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
                                T4interSetup(GPT2, 1 / samplerate);
                                return true;
                                break;
    case settingProcessingFreq: command.remove(0, 20);
                                processingRate = max(1, command.toFloat());
                                T4interSetup(GPT1, 1 / processingRate);
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
 *
 *  @param command Command (in ASCII format) as received from PC
 *  @return numerical identifier for the respective command.  
 */
int checkCommand(String command) {
  if(command.startsWith("set oversamples "))      {return settingOversamples;}
  if(command.startsWith("set dataSize "))         {return settingSize;}
  if(command.startsWith("set samplerate "))       {return settingSpectralFreq;}
  if(command.startsWith("set processing rate "))  {return settingProcessingFreq;}
  if(command.startsWith("set signalType "))       {return settingSignalType;}
  if(command.startsWith("send data"))             {return commandRequest;}
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
