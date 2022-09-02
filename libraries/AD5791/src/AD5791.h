/**	@file AD5791.h
 *	@brief Library for using an AD5791 with a Teensy 4.0 via SPI. Used in the course "digital signal- and measurement data processing".
 *	
 *	This library is rather simple due to the converter being very simple as well.
 *  
 *  @author Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
 *  @author Philipp Rahe (prahe@uos.de)
 *  @date 06.01.2022
 *  @version 2.1
 *	
 *	In order for this library to work correctly, there are some variables that have to be defined externally 
 *	(for the course "digital signal- and measurement data processing" this is done in the DSMV-Board library):
 *		- uint32_t ccRate: Frequency of the timer counter
 *		- uint8_t TimerPin: Pin for measuring timing
 *		- uint8_t SYNC_AD5791: SYNC pin of the AD5791
 *		- uint8_t RESET_AD5791: RESET pin of the AD5791
 *		- uint8_t CLR_AD5791: CLR pin of the AD5791
 *		- uint8_t LDAC_AD5791: LDAC pin of the AD5791
 *		- uint8_t SCLK_AD5791: SCLK pin of the AD5791
 *		- uint8_t MOSI_AD5791: MOSI pin of the AD5791
 *  
 *  @par Changelog
 *		- 06.01.2022 :	Added documentation on external definitions
 *		- 05.01.2022 :  added support for configuration via USB, added function to set clearcode voltage to a custom value
 *						and fully translated documentation into English
 *		- 28.07.2020 :	first version for board v0.1
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

#ifndef AD5791_h
#define AD5791_h

#include "Arduino.h"

/** @brief Initializes the AD5791 with the given voltage range.
 *  
 *  @param minV Minimum output voltage.
 *  @param maxV Maximum output voltage.
 */
void AD5791initialize(float minV, float maxV);

/**	@brief Sets the AD5791 to regular operating mode.
 */
void AD5791standardMode();

/** @brief Sets the AD5791 output the voltage stored in the clearcode register (default voltage).
 */
void AD5791clearOutput();

/** @brief Sets the voltage stored in the clearcode register (default voltage) to the given value (V).
 *  
 *  @param voltage Voltage to be stored in the clearcode register (V).
 */
void AD5791setDefaultVoltage(float defaultVoltage);

/** @brief Clamps the output of the AD5791 to ground.
 */
void AD5791off();

/** @brief Writes 3 bytes via the SPI bus (MSB first).
 *  
 *  @param data Data to write (padded with zeros at the front).
 */
void AD5791regWrite(uint32_t data);

/** @brief Sets the output voltage of the AD5791 to the given value (V).
 *  
 *  @param voltage Voltage to be output by the AD5791 (V).
 */
void AD5791setVoltage(float voltage);

/** @brief Sends the given byte via the SPI bus (MSB first).
 *  
 *  @param byte Byte to be sent.
 */
void AD5791sendSPI(uint8_t byte);

/**	@brief Checks a String for a command to change a setting of the AD5791.
 *	
 *	@param a String to be checked.
 *	@return Whether the command was successfully processed.
 */
bool AD5791checkUpdate(String a);

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

#endif
