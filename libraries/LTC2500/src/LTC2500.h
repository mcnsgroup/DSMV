/**	@file LTC2500.h
 *	@brief Library for using an LTC2500 with a Teensy 4.0 via SPI. Used in the course "digital signal- and measurement data processing".
 *	
 *	This library provides both a means of reading the value directly and via a timing based interrupt
 *	(provided that the used timer has been set up already; in the course "digital signal- and measurement data processing" 
 *	this is done by the T4 library).
 *	It also comes with integrated oversampling for the interrupt based reading and is able to configure the preset filters of the LTC2500.
 *	
 *	In order for this library to work correctly, there are some variables that have to be defined externally 
 *	(for the course "digital signal- and measurement data processing" this is done in the DSMV-Board library):
 *		- uint32_t ccRate: Frequency of the timer counter
 *		- uint8_t TimerPin: Pin for measuring timing
 *		- uint8_t DebugPin: Pin for debug mode 
 *		- uint8_t MCLK_LTC2500:	MCLK pin of the LTC2500
 *		- uint8_t RDLA_LTC2500:	RDLA pin of the LTC2500
 *		- uint8_t RDLB_LTC2500: RDLB pin of the LTC2500
 *		- uint8_t PRE_LTC2500: PRE pin of the LTC2500
 *		- uint8_t DRL_LTC2500: DRL pin of the LTC2500
 *		- uint8_t BUSY_LTC2500: BUSY indicator of the LTC2500
 *		- uint8_t SCLK_LTC2500: Serial clock of the LTC2500
 *		- uint8_t MOSI_LTC2500: MOSI pin of the LTC2500
 *		- uint8_t MISO_LTC2500: MISO pin of the LTC2500
 *  
 *  @author Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
 *  @author Philipp Rahe (prahe@uos.de)
 *  @date 06.01.2022
 *  @version 2.1
 *  
 *  @par Changelog
 *		- 06.01.2022 :	Added documentation on external definitions
 *		- 05.01.2022 :  Added support for configuration via USB,
 *						added option to use library with pre 1.1 versions of the board,
 *						bug fixes, removed deprecated code,
 *						fully translated documentation of the .cpp file to English
 *  	- 26.05.2021:	Documentation translated into English
 *		- 2021:			Added functionality to configure internal filters.
 *  	- 2020 - 2021:	Added integrated oversampling
 *  	- 		 2020:	first version for board v0.1
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

#ifndef LTC2500_h
#define LTC2500_h

#include "Arduino.h"

#define noLatencyOutput 0	/**< @brief Unfiltered output. */
#define filteredOutput 1	/**< @brief Filtered output. */
#define silent 2			/**< @brief No output (can be useful, if the SPI-bus is used by multiple devices). */
#define sinc1 1				/**< @brief Code for filter type sinc^1. */
#define sinc2 2				/**< @brief Code for filter type sinc^2. */
#define sinc3 3				/**< @brief Code for filter type sinc^3. */
#define sinc4 4				/**< @brief Code for filter type sinc^4. */
#define ssinc 5				/**< @brief Code for filter type ssinc. */
#define flatPass 6			/**< @brief Code for filter type flat passband. */
#define averaging 7			/**< @brief Code for filter type averaging. */

/** @brief Define the DSMV board version (version number *10: 1, 10, 11, 20) **/
#define BOARD_VERSION 20

/**	@brief Initializes the LTC2500 with the given settings.
 *	
 *	@param samplerate Number of conversions per second.
 *	@param numOversamples Number of oversamples.
 *	@param timer Timer counter to be used for the interrupt: 0 (GPT1) or 1 (GPT2).
 *	@param mode Output mode: no latency, unfiltered output (noLatencyOutput) of filtered output (filteredOutput).
 *	@param timing Specifies whether to use the timing pin.
 *	@param noSkip Specifies whether the ISR will be cancelled if data is being read too fast to be sent.
 */
void LTC2500initialize(uint32_t samplerate, uint32_t numOversamples, uint8_t timer, uint8_t mode, bool timing, bool noSkip);

/**	@brief Initializes the LTC2500 with the given settings and assumes default values for timing and noSkip.
 *	
 *	@param samplerate Number of conversions per second.
 *	@param numOversamples Number of oversamples.
 *	@param timer Timer counter to be used for the interrupt: 0 (GPT1) or 1 (GPT2).
 *	@param mode Output mode: no latency, unfiltered output (noLatencyOutput) of filtered output (filteredOutput).
 */
void LTC2500initialize(uint32_t samplerate, uint32_t numOversamples, uint8_t timer, uint8_t mode);

/**	@brief Initializes the LTC2500 without an interrupt.
 *	
 *	@param mode Output mode: no latency, unfiltered output (noLatencyOutput) of filtered output (filteredOutput).
 *	@param timing Specifies whether to use the timing pin.
 */
void LTC2500initialize(uint8_t mode, bool timing);

/**	@brief Initializes the LTC2500 without an interrupt and standard values.
 */
void LTC2500initialize();

/**	@brief Checks a String for a command to change a setting of the LTC2500.
 *	
 *	@param a String to be checked.
 *	@return Whether the command was successfully processed.
 */
bool LTC2500checkUpdate(String a);

/**	@brief Updates the settings of the LTC2500.
 *	
 *	@param samplerate Number of conversions per second.
 *	@param numOversamples Number of oversamples.
 *	@param timer Timer counter to be used for the interrupt: 0 (GPT1) or 1 (GPT2).
 *	@param mode Output mode: no latency, unfiltered output (noLatencyOutput) of filtered output (filteredOutput).
 *	@param timing Specifies whether to use the timing pin.
 *	@param noSkip Specifies whether the ISR will be cancelled if data is being read too fast to be sent.
 */
void LTC2500update(uint32_t samplerate, uint32_t numOversamples, uint8_t timer, uint8_t mode, bool timing, bool noSkip);

/**	@brief Updates the samplerate of the LTC2500.
 *	
 *	@param samplerate Number of conversions per second.
 */
void LTC2500updateSamplerate(uint32_t samplerate);

/**	@brief Updates the number of oversamples of the LTC2500.
 *	
 *	@param numOversamples Number of oversamples.
 */
void LTC2500updateOversamples(uint32_t numOversamples);

/**	@brief Updates the timer counter to be used for the interrupt.
 *	
 *	@param timerCounter Timer counter to be used for the interrupt: 0 (GPT1) or 1 (GPT2).
 */
void LTC2500updateTimer(uint32_t timer);

/**	@brief Updates the output mode of the LTC2500.
 *	
 *	@param mode Output mode: no latency, unfiltered output (noLatencyOutput) of filtered output (filteredOutput).
 */
void LTC2500updateOutputMode(uint8_t mode);

/**	@brief Read a value from the LTC2500.
 *	
 *	@return Raw value from the LTC2500 in int32_t format.
 */
int32_t LTC2500readValue();

/**	@brief Checks whether the current buffer is full and possibly sends it to the PC.
 * 
 * If the PC doesn't read it, this takes approximately 100 ns.
 */
void LTC2500sendDataToPC();

/**	@brief Configures the internal filter.
 *	
 *	@param type Filter type: 1 (sinc^1), 2 (sinc^2), 3 (sinc^3), 4 (sinc^4), 5 (ssinc), 6 (flat passband), 7 (averaging).
 *	@param downsampling Exponent of the downsampling factor (ranges from 2 to 14).
 *	@param DGE Specifies whether to use digital gain expansion.
 *	@param DGC Specifies whether to use digital gain compression.
 */
void LTC2500configureFilter(int type, int downsampling, bool DGE, bool DGC);

/**	@brief Sends a command via SPI to the LTC2500.
 *
 *	@param command The command to be sent (12 bits).
 */
void LTC2500sendCommand(int command);

/**	@brief Read and write access to the low byte.
 *	
 *	This macro relies on pointer arithmetic, so be sure
 *	the datatype is well defined!
 *	
 *	@param v Any numerical value. Make sure the value is as long as the requested byte!
 */
#define LBYTE(v)  (*((unsigned char*) (&v)))

/**	@brief Read and write access to the low+1 byte.
 *	
 *	This macro relies on pointer arithmetic, so be sure
 *	the datatype is well defined!
 *	
 *	@param v Any numerical value. Make sure the value is as long as the requested byte!
 */
#define HBYTE(v)  (*((unsigned char*) (&v) + 1))

/**	@brief Read and write access to the low+2 byte.
 *	
 *	This macro relies on pointer arithmetic, so be sure
 *	the datatype is well defined!
 *	
 *	@param v Any numerical value. Make sure the value is as long as the requested byte!
 */
#define H2BYTE(v) (*((unsigned char*) (&v) + 2))

/**	@brief Read and write access to the low+3 byte.
 *	
 *	This macro relies on pointer arithmetic, so be sure
 *	the datatype is well defined!
 *	
 *	@param v Any numerical value. Make sure the value is as long as the requested byte!
 */
#define H3BYTE(v) (*((unsigned char*) (&v) + 3))

#endif
