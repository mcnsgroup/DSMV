/**	@file AD4020.h
 *	@brief Library for using an AD4020 with a Teensy 4.0 via SPI. Used in the course "digital signal- and measurement data processing".
 *	
 *	This library provides both a means of reading the value directly and via a timing based interrupt
 *	(provided that the used timer has been set up already; in the course "digital signal- and measurement data processing"
 *	this is done by the T4 library).
 *	It also comes with integrated oversampling for the interrupt based reading.
 *	
 *	In order for this library to work correctly, there are some variables that have to be defined externally 
 *	(for the course "digital signal- and measurement data processing" this is done in the DSMV-Board library):
 *		- uint32_t ccRate: Frequency of the timer counter
 *		- uint8_t TimerPin: Pin for measuring timing
 *		- uint8_t DebugPin: Pin for debug mode
 *		- uint8_t CNV_AD4020: CNV pin of the AD4020
 *		- uint8_t SCLK_AD4020: Serial clock pin of the AD4020
 *		- uint8_t MOSI_AD4020: MOSI pin of the AD4020
 *		- uint8_t MISO_AD4020: MISO pin of the AD4020
 *  
 *  @author Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
 *  @author Philipp Rahe (prahe@uos.de)
 *  @date 06.01.2022
 *  @version 2.1
 *  
 *  @par Changelog
 *		- 06.01.2022 :	Added documentation on external definitions
 *		- 05.01.2022 :  Fully translated documentation of the .cpp file to English and removed deprecated code
 *		- 02.06.2021 :	Minor bug fixes
 *  	- 26.05.2021 :	Documentation translated into English and added support for configuration via USB
 *  	- 2020 - 2021 :	Added integrated oversampling
 *  	- 		 2020 :	first version for board v0.1
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

#ifndef AD4020_h
#define AD4020_h

#include "Arduino.h"

// Pins
extern uint8_t TimerPin;	/**< @brief Pin for timing mesurement purposes. */
extern uint8_t DebugPin;	/**< @brief Pin for indicating that the converter has stopped operating, i. e. due to a buffer overflow. */
extern uint8_t CNV_AD4020;	/**< @brief CNV Pin. */
extern uint8_t SCLK_AD4020;	/**< @brief Pin for the serial clock. */
extern uint8_t MOSI_AD4020;	/**< @brief Mosi Pin. */
extern uint8_t MISO_AD4020;	/**< @brief Miso Pin. */

/**	@brief Initializes the AD4020 with the given settings.
 *	
 *	@param samplerate Number of conversions per second.
 *	@param numOversamples Number of oversamples.
 *	@param timer Timer counter to be used for the interrupt: 0 (GPT1) or 1 (GPT2).
 *	@param timing Specifies whether to use the timing pin.
 *	@param noSkip Specifies whether the ISR will be cancelled if data is being read too fast to be sent.
 */
void AD4020initialize(uint32_t samplerate, uint32_t numOversamples, uint8_t timer, bool timing, bool noSkip);

/**	@brief Initializes the AD4020 with the given settings and assumes default values for timing and noSkip.
 *	
 *	@param samplerate Number of conversions per second.
 *	@param numOversamples Number of oversamples.
 *	@param timer Timer counter to be used for the interrupt: 0 (GPT1) or 1 (GPT2).
 */
void AD4020initialize(uint32_t samplerate, uint32_t numOversamples, uint8_t timer);

/**	@brief Initializes the AD4020 without an interrupt.
 *	
 *	@param timing Specifies whether to use the timing pin.
 */
void AD4020initialize(bool timing);

/**	@brief Initializes the AD4020 without an interrupt and standard values.
 */
void AD4020initialize();

/**	@brief Checks a String for a command to change a setting of the AD4020.
 *	
 *	@param a String to be checked.
 *	@return Whether the command was successfully processed.
 */
bool AD4020checkUpdate(String a);

/**	@brief Updates the settings of the AD4020.
 *	
 *	@param samplerate Number of conversions per second.
 *	@param numOversamples Number of oversamples.
 *	@param timer Timer counter to be used for the interrupt: 0 (GPT1) or 1 (GPT2).
 *	@param timing Specifies whether to use the timing pin.
 *	@param noSkip Specifies whether the ISR will be cancelled if data is being read too fast to be sent.
 */
void AD4020update(uint32_t samplerate, uint32_t numOversamples, uint8_t timer, bool timing, bool noSkip);

/**	@brief Updates the samplerate of the AD4020.
 *	
 *	@param samplerate Number of conversions per second.
 */
void AD4020updateSamplerate(uint32_t samplerate);

/**	@brief Updates the number of oversamples of the AD4020.
 *	
 *	@param numOversamples Number of oversamples.
 */
void AD4020updateOversamples(uint32_t numOversamples);

/**	@brief Updates the timer counter to be used for the interrupt.
 *	
 *	@param timerCounter Timer counter to be used for the interrupt: 0 (GPT1) or 1 (GPT2).
 */
void AD4020updateTimer(uint8_t timer);

/**	@brief Updates the setting for whether to use the timing pin.
 *	
 *	@param timing Whether to use the timing pin .
 */
void AD4020updateTiming(bool timing);

/**	@brief Updates the setting for whether the ISR will be cancelled if data is being read too fast to be sent..
 *	
 *	@param noSkip Whether the ISR will be cancelled if data is being read too fast to be sent.
 */
void AD4020updateNoSkip(bool noSkip);

/**	@brief Read a value from the AD4020.
 *	
 *	@return Raw value from the AD4020 in int32_t format.
 */
int32_t AD4020readValue();

/**	@brief Checks whether the current buffer is full and possibly sends it to the PC.
 * 
 * If the PC doesn't read it, this takes approximately 100 ns.
 */
void AD4020sendDataToPC();

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
