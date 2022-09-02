/** @file DSMV_Board.h
 *  @brief Pin definitions for the <b>DSMV board</b> used in the course "digital signal- and measurement data processing". 
 *
 *	The DSMV board contains: 
 *		- a Teensy 4.0 microcontroller 
 *		- AD4020 analog digital converter
 *		- LTC2500 analog digital converter
 *		- AD5791 digital analog converter
 *		- Schmitt-trigger input
 *		- 3 buttons
 *		- 3 LEDs
 *
 *  The board was developed by the workshop for electronics and IT 
 *  at Fachbereich Physik, Universität Osnabrück 
 *  (<a href="https://www.physik.uni-osnabrueck.de/fachbereich/werkstaetten/werkstatt_fuer_elektronik_it.html">Link</a>). 
 *
 *  Currently, four versions of the boards exist that have slightly different pin definitions.
 *  These are selected below by corresponding flags given by the board version number BOARD_VERSION. 
 *  
 *  @author Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
 *  @author Philipp Rahe (prahe@uos.de)
 *  @date 17.05.2021
 *  @version 2.0
 *  
 *  @par Changelog 
 *		- 06.01.2021 :	Added backwards compatibility with older versions of the board (different pin layouts)
 *  	- 12.05.2021 :	precompiler flags for board versions introduced
 *  	- 05.05.2021 :	updated to board v2.0
 *  	- June  2020 :	first version for board v1.0
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

#include "T4.h"

#ifndef DSMV_Board_h
#define DSMV_Board_h

/** @brief Define the DSMV board version (version number *10: 1, 10, 11, 20) **/
#define BOARD_VERSION 20

#if BOARD_VERSION == 01		// Board version 0.1 (initial version)
#elif BOARD_VERSION == 10	// Board version 1.0
#elif BOARD_VERSION == 11	// Board version 1.1
#elif BOARD_VERSION == 20	// Board version 2.0 (current version)
const uint8_t AD4020_CNV = 0;		/**< @brief CNV pin of the AD4020. */
const uint8_t LTC2500_RDLB = 1;		/**< @brief RDLB pin of the LTC2500. */
const uint8_t LTC2500_RDLA = 2;		/**< @brief RDLA pin of the LTC2500. */
const uint8_t LTC2500_BUSY = 3;		/**< @brief BUSY pin of the LTC2500. */
const uint8_t LTC2500_DRL = 4;		/**< @brief DRL pin of the LTC2500. */
const uint8_t LTC2500_SYNC = 5;		/**< @brief SYNC pin of the LTC2500. */
const uint8_t LTC2500_MCLK = 6;		/**< @brief MCLK pin of the LTC2500. */
const uint8_t LTC2500_PRE = 7;		/**< @brief PRE pin of the LTC2500. */
const uint8_t SCHMITT_TRIGGER = 8;	/**< @brief Schmitt-Trigger input pin. */
const uint8_t LED_1 = 9;		/**< @brief LED 1 input pin. */
const uint8_t BUTTON_3 = 10;		/**< @brief Button 1 input pin. */
const uint8_t MOSI_ADC = 11;		/**< @brief MOSI pin for SPI to ADCs. */
const uint8_t MISO_ADC = 12;		/**< @brief MISO pin for SPI to ADCs. */
const uint8_t SCLK_ADC = 13;		/**< @brief SCLK pin for SPI to ADCs. */
const uint8_t ADC_TEENSY = 14;		/**< @brief Input pin internal ADC. */
const uint8_t BUTTON_1 = 15;		/**< @brief Button 2 input pin. */
const uint8_t LED_2 = 16;		/**< @brief LED 2 input pin. */
const uint8_t BUTTON_2 = 17;		/**< @brief Button 3 input pin. */
const uint8_t LED_3 = 18;		/**< @brief LED 3 input pin. */
const uint8_t DAC_TEENSY = 19;		/**< @brief Internal DAC (PWM output). */
const uint8_t AD5791_SYNC = 20;		/**< @brief SYNC pin of the AD5791. */
const uint8_t AD5791_RESET = 21;	/**< @brief RESET pin of the AD5791. */
const uint8_t AD5791_CLR = 22;		/**< @brief CLR pin of the AD5791. */
const uint8_t AD5791_LDAC = 23;		/**< @brief LDAC pin of the AD5791. */
const uint8_t MISO_DAC = 34;		/**< @brief MISO pin for SPI to DAC. */
const uint8_t MOSI_DAC = 35;		/**< @brief MOSI pin for SPI to DAC. */
const uint8_t SCLK_DAC = 37;		/**< @brief SCLK pin for SPI to DAC. */
#else
//const uint8_t AD4020_CNV = 1;		/**< @brief CNV pin of the AD4020. */
#endif

/** @brief Sets all output pins of Teensy 4.0
 *
 *  This function is usually called in the @verbatim setup()@endverbatim function of the 
 *  Arduino sketch. 
 */
void setOutputPins();


/** @brief Reads the value of the Schmitt-trigger input pin.
 * 
 *  @return Value of the input (HIGH or LOW).
 */
bool readSchmitt();

#endif
