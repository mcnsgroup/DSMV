/**	@file T4.h
 *	@brief This library contains a lot of functions to simplify programming the <b>Teensy 4.0</b>. It is used in the course "digital signal- and measurement data processing".
 *	
 *	Notable features are:
 *		- serial interfacing with peripheral devices via SPI
 *		- serial interfacing with a PC (interrupt based)
 *		- timing based interrupts and a 7 ns resolution clock
 *		- extracting specific bytes from an arbitrary data type
 *		- a function generator
 *	
 *	In order for this library to work correctly, there are some variables that have to be defined externally 
 *	(for the course "digital signal- and measurement data processing" this is done in the DSMV-Board library):
 *		- uint8_t T4mosi: MOSI pin for SPI communication
 *		- uint8_t T4miso: MISO pin for SPI communication
 *		- uint8_t T4sclk: Clock pin for SPI communication
 *		- uint8_t SucessPin: Pin for measuring timing and displaying a succesful processing of a command
 *		- uint8_t FailPin: Pin for debugging and displaying a failed processing of a command
 *	
 *	@author Lukas Freudenberg (lfreudenberg@uni-osnabrueck.de)
 *	@author Philipp Rahe (prahe@uos.de)
 *	@date 06.01.2021
 *	@version 2.1
 *	
 *	@par Changelog
 *		- 06.01.2022 :	Added documentation on external definitions
 *		- 08.06.2021: integrated buffer for 32-bit data types
 *		- 26.05.2021: updated documentation to include byte macros
 *		- 17.05.2021: documentation translated into English
 *		- meantime: added function generator, timing based interrupts, clock, interrupt based serial communication and byte extraction
 *		- November 2019: first version
 *	
 *	@copyright 
 *	Copyright 2021 Lukas Freudenberg, Philipp Rahe 
 *	
 *	@par License
 *	@parblock
 *	Permission is hereby granted, free of charge, to any person 
 *	obtaining a copy of this software and associated documentation 
 *	files (the "Software"), to deal in the Software without 
 *	restriction, including without limitation the rights to use, copy,
 *	modify, merge, publish, distribute, sublicense, and/or sell 
 *	copies of the Software, and to permit persons to whom the Software 
 *	is furnished to do so, subject to the following conditions:
 *	
 *	The above copyright notice and this permission notice shall be 
 *	included in all copies or substantial portions of the Software.
 *	
 *	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
 *	EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
 *	OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
 *	NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
 *	HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
 *	WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
 *	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR 
 *	OTHER DEALINGS IN THE SOFTWARE.
 *	@endparblock
 *
 */

#ifndef T4_h
#define T4_h

#include "Arduino.h"
#include <stdint.h>

#define NOP0 __asm__ __volatile__ ("nop\n\t" "nop\n\t")	/**< @brief Idle for 2^0 cycles. */
#define NOP1 NOP0; NOP0									/**< @brief Idle for 2^1 cycles. */
#define NOP2 NOP1; NOP1									/**< @brief Idle for 2^2 cycles. */
#define NOP3 NOP2; NOP2									/**< @brief Idle for 2^3 cycles. */
#define NOP4 NOP3; NOP3									/**< @brief Idle for 2^4 cycles. */
#define NOP5 NOP4; NOP4									/**< @brief Idle for 2^5 cycles. */
#define NOP6 NOP5; NOP5									/**< @brief Idle for 2^6 cycles. */
#define NOP7 NOP6; NOP6									/**< @brief Idle for 2^7 cycles. */
#define NOP8 NOP7; NOP7									/**< @brief Idle for 2^8 cycles. */
#define NOP9 NOP8; NOP8									/**< @brief Idle for 2^9 cycles. */

// constants to improve readability
#define T4maxBaud	4000000	/**< @brief Maximum baudrate. */
#define T4maxPin	39		/**< @brief Number of the last pin on the Teensy 4.0. */
#define T4maxSigLen	16384	/**< @brief Maximum length of the signal array. */
#define GPT1 0				/**< @brief General Purpose Timer 1. */
#define GPT2 1				/**< @brief General Purpose Timer 2. */
#define T4ccRate 150000000	/**< @brief Counter clock rate (Hz). */
#define T4maxSerialFuncs 20	/**< @brief Maximum number of functions to be executed while checking the seriel Buffer. */
// to be used in conjunction with &=
#define SCMR1_CLK_RT	0xFFFFFFBF	/**< @brief Use root clock for timing (150 MHz). */
#define PERCLK_DIV_1	0xFFFFFF80	/**< @brief Set divider for the peripheral clock to 1. */
#define SCMR1_CLK_OSC	0xFFFFFFCF	/**< @brief Use oscillator clock for the GPT (24 MHz). */
#define GPT_CR_DIS		0xFFFFFFFE	/**< @brief Deactivate the GPT. */
// to be used in conjunction with |=
#define GPT_CR_ENA		0x00000001	/**< @brief Activate the GPT. */
#define GPT_CR_PER		0x00000040	/**< @brief Use peripheral clock for the GPT (150 MHz if root clock is used). */
#define GPT_SR1			0x00000001	/**< @brief Reset interrupt 1 in the status register of the GPT. */
#define GPT_SR2			0x00000002	/**< @brief Reset interrupt 2 in the status register of the GPT. */
#define GPT_SR3			0x00000004	/**< @brief Reset interrupt 3 in the status register of the GPT. */
#define CGR1_GPT1		0x00F00000	/**< @brief Activate clocks for GPT1 module. */
#define CGR1_GPT2		0x0F000000	/**< @brief Activate clocks for GPT2 module. */
#define GPT_OM1_TOGGLE	0x00100000	/**< @brief Toggle the set pin at the output compare 1 of the GPT. */
#define GPT_OM2_TOGGLE	0x00800000	/**< @brief Toggle the set pin at the output compare 2 of the GPT. */
#define GPT_OM3_TOGGLE	0x04000000	/**< @brief Toggle the set pin at the output compare 3 of the GPT. */
// others
#define GPT_OC1		0x00000001	/**< @brief Bit corresponding to enabling the output compare 1 of the GPT and its interrupt flag. */
#define GPT_OC2		0x00000002	/**< @brief Bit corresponding to enabling the output compare 2 of the GPT and its interrupt flag. */
#define GPT_OC3		0x00000004	/**< @brief Bit corresponding to enabling the output compare 3 of the GPT and its interrupt flag. */

// special functions for interrupts

/**	@brief Initializes the timer counters GPT1 and GPT2.
 *	
 *	This function is usually called in the @verbatim setup()@endverbatim function of the Arduino sketch.
 */
void T4TimerInit();

/**	@brief Sets the interval of the given timer counter (s).
 *	
 *	This function can be called in the @verbatim setup()@endverbatim function or at any time while the program is running to change the interval.
 *	Important: The GPT1 interrupt has priority over the GPT2 interrupt, should they occur at the same time.
 *
 *  @param timer Timer counter to be used: 0 (GPT1) or 1 (GPT2).
 *  @param compare Value that the timer counter has to reach in order to generate the interrupt.
 */
void T4interSetup(uint8_t timer, float interval);

/**	@brief Configures the function to be executed at the interrupt of the GPT1.
 *	
 *	@param func Function to be executed.
 */
void T4setInterrupt1(void (*func)());

/**	@brief Configures the function to be executed at the interrupt of the GPT2.
 *	
 *	@param func Function to be executed.
 */
void T4setInterrupt2(void (*func)());

// Shortcuts for Arduino functions and more

/**	@brief Configures the given pins aus outputs.
 *	
 *	@param outPins Array containing the numbers of the pins.
 *	@param size Length of the array.
 */
void T4pinSetup(const int outPins[], int size);

/**	@brief Sets the resolution of the PWM outputs in bits (standard: 10 bits, maximum 12 bits).
 *	
 *	@param res Resolution in bits.
 */
void T4awr(int res);

/**	@brief Sets the output voltage of the given pin to the given value (V).
 *	
 *	@param pin Number of the pin.
 *	@param voltage Output voltage (V): minimum 0V, maximum 3.3V.
 */
void T4awV(int pin, float voltage);

/**	@brief Sets the resolution of the analog inputs in bits (standard: 10 bits, maximum 12 bits).
 *	
 *	@param res Bitauflösung der analogen Eingänge.
 */
void T4arr(int res);

/**	@brief Sets the number of oversamples for reading an analog value.
 *	
 *	@param samples Anzahl der gemittelten Samples.
 */
void T4aravg(int samples);

/**	@brief Reads an analog value from a given pin and converts it into a voltage (V).
 *	
 *	@param pin Number of the pin to be read.
 *	@return Read voltage (V).
 */
float T4arV(int pin);

/**	@brief Writes a digital value to a given pin as fast as possible.
 *	
 *	@param pin Number of the pin to write to.
 *	@param value Value to be written (HIGH or LOW).
 */
void T4dw(int pin, int value);

/**	@brief Writes an analog value to a given pin.
 *	
 *	@param pin Number of the pin to write to.
 *	@param value Value to be written.
 */
void T4aw(int pin, int value);

/**	@brief Reads a digital value from a given pin as fast as possible.
 *	
 *	@param pin Number of the pin to be read.
 */
int T4dr(int pin);

/**	@brief Reads an analog value from a given pin.
 *	
 *	@param pin Number of the pin to be read.
 *	@return Voltage value scaled from 0...3 V to the integer range 0...2^(analog read resolution in bits).
 */
int T4ar(int pin);

// other useful things for the microcontroller

/**	@brief Inverts the digital output value of a given pin.
 *	
 *	@param pin Number of the pin to invert.
 */
void T4toggle(int pin);

/**	@brief Stops the program that is currently running and power down all outputs.
 *	
 *	This also includes interrupts and should only be used for debugging purposes or emergencies.
 */
void T4stop();

/**	@brief Sends a given byte with the given clock speed via the SPI bus (MSB first) and reads the answer from any connected device(s).
 *	
 *	The variable clock speed feature has not been implemented yet. It currently operates at a frequency of 6.8 MHz.
 *	
 *	@param byte Byte to be sent.
 *	@param clkSpeed Frequency of the serial clock (Hz) (not implemented yet).
 *	@return Byte read back from the connected device(s).
 */
uint8_t T4SPIsend(uint8_t byte, uint8_t clkSpeed);

/**	@brief Sends a given byte with the given clock speed via the SPI bus (MSB first) and ignores the potential read back.
 *	
 *	The variable clock speed feature has not been implemented yet. It currently operates at a frequency of 54 MHz.
 *	
 *	@param byte Byte to be sent.
 *	@param clkSpeed Frequency of the serial clock (Hz) (not implemented yet).
 */
void T4SPIsendFast(uint8_t byte, uint8_t clkSpeed);

/**	@brief Reads one byte with the given clock speed via the SPI bus (MSB first).
 *	
 *	The variable clock speed feature has not been implemented yet. It currently operates at a frequency of 11.6 MHz.
 *	
 *	@param clkSpeed Frequency of the serial clock (Hz) (not implemented yet).
 *	@return Byte that was read.
 */
uint8_t T4SPIread(uint8_t clkSpeed);

/**	@brief Calculates the current time (s) since program start from the GPT1 (resolution: up to 7ns if the fastest clock setting is chosen).
 *  
 *  @return Current time since program start (s).
 */
double T4getTime();

// Signal generator

/**	@brief Adds a frequency with given amplitude and phase to the signal.
 *	
 *	@param freq Frequency to be added.
 *	@param amp Amplitude of the frequency to be added.
 *	@param ph Phase of the frequency to be added.
 */
void T4addSignal(float freq, float amp, float ph);

/**	@brief Resets the signal of the generator to zero.
 *	
 *	This also resets the number of frequencies.
 */
void T4clearSignal();

/**	@brief Calculates the current value of the signal generator.
 *	
 *	@return Value of the signal at the current time.
 */
double T4sigValue();

/**	@brief Calculates the value of the signal generator at the given time.
 *	
 *	@param t Time to calculate the value at (s).
 *	@return Value of the signal at the given time.
 */
double T4sigValue(double t);

extern int T4sigLen;		/**< @brief Current number of data points in the signal. */
extern float T4sig[];		/**< @brief Array to store the values of the signal generator. */
extern uint8_t T4pulse[];	/**< @brief Array to store the signs of the signal for a rectangular pulse. */

/**	@brief Calculates the points of the signal with a given amplitude and writes them into an array with a length matching its period.
 *	
 *	If the frequency is too low, the rest of the signal gets cut off.
 *	
 *	@param values Array to write the values to.
 *	@param amp Amplitude of the signal.
 */
void T4sigTable(float values[], float amp);

/**	@brief Calculates the points of the signal with amplitude 1 and writes them into an array with a length matching its period.
 *	
 *	If the frequency is too low, the rest of the signal gets cut off.
 *	
 *	@param values Array to write the values to.
 */
void T4sigTable(float values[]);

/**	@brief Calculates the points of the rectangular pulse and writes them into an array with a length matching its period.
 *	
 *	If the frequency is too low, the rest of the signal gets cut off.
 *	
 *	@param values Array to write the values to.
 */
void T4pulseTable(uint8_t values[]);

/**	@brief Sets the parameters for a frequency modulated signal.
 *  
 *  @param freqC Carrier frequency of the signal.
 *  @param ampC Amplitude of the signal.
 *  @param freqM Bandwidth of the frequency modulation.
 */
void T4setFM(float freqC, float ampC, float freqM);

/**	@brief Calculates the current value of the frequency modulated signal.
 *	
 *	@return Value of the signal at the current time.
 */
double T4fmValue();

/**	@brief Calculates the value of the frequency modulated signal at the given time.
 *	
 *	@param t Time to calculate the value at (s).
 *	@return Value of the signal at the given time.
 */
double T4fmValue(double t);

/**	@brief Gets the memory adress of the first byte of an object.
 *  
 *	The adress can then be written into a pointer. Example:
 *	@verbatim String a;
	uint8_t* ptr = T4toBytes(a);@endverbatim
 */
#define T4toBytes (uint8_t*) &

/**	@brief Converts an int32_t from the standard representation (two's complement) to the format sign + absolute value.
 *	
 *	@param a Value to be converted.
 *	@return Converted value.
 */
int32_t T4toSignMag(int32_t a);

/**	@brief Converts an int32_t from the standard representation (two's complement) to the format excess 2^31.
 *	
 *	@param a Value to be converted.
 *	@return Converted value.
 */
int32_t T4toExzess(int32_t a);

/**	@brief Converts an int32_t from the standard representation (two's complement) to the format one's complement.
 *	
 *	@param a Value to be converted.
 *	@return Converted value.
 */
int32_t T4to1Comp(int32_t a);

// serial communication with the PC

/**	@brief Starts the serial communication with the given baudrate.
 *	
 *	If the connection to the PC is done directly via USB (without a programmer in between), this function doesn't serve a purpose (at least with the Teensy 4.0).
 *	
 *	@param baud Baudrate in symbols per second ().
 */
void T4sBg(long baud);

/**	@brief Starts the serial communication with a baudrate of 9600.
 *	
 *	If the connection to the PC is done directly via USB (without a programmer in between), this function doesn't serve a purpose (at least with the Teensy 4.0).
 */
void T4sBg();

/**	@brief Prints an object via the serial interface (matches Serial.print()).
 */
#define T4p Serial.print

/**	@brief Prints an object via the serial interface followed by a newline character (matches Serial.println()).
 */
#define T4pln Serial.println

/**	@brief Sends something via the serial interface (matches Serial.write).
 */
#define T4sw Serial.write

/**	@brief Reads something from the serial interface (matches Serial.read).
 */
#define T4sr Serial.read

/**	@brief Gets the number ob bytes available to be read at the serial interface (matches Serial.available).
 */
#define T4sa Serial.available

/**	@brief Returns the content of the internal serial buffer.
 *	
 *	@return Content of the buffer as character array in the String format.
 */
char* T4serialBuffer();

/**	@brief Clears the content of the internal serial buffer.
 */
void T4clearSerialBuffer();

/**	@brief Executes the functions that have been set to check the serial buffer.
 *	
 *	The functions recieve the content of the serial buffer one by one until one of them returns <b>true</b>
 *	(indicating that the String was successfully processed, in this case the externally specified pin outputs a pulse),
 *	or all functions return false (indicating that the input could not be processed, which also causes a pulse on the respective pin).
 *	Either way, the serial buffer is cleared.
 */
void T4checkSerialBuffer();

/**	@brief Sets the duration of the pulse to indicate a successful (or unsuccessful) processing of the serial buffer.
 *	
 *	@param t Pulse duration (ms).
 */
void T4setSerialPulseTime(int t);

/**	@brief Adds a function to the array of functions to check the serial buffer.
 *	
 *	@param func Function to be added (must take a String as its parameter and return a bool).
 */
void T4addSerialFunc(bool (*func)(String a));

/**	@brief Sets the length of the cyclic buffer.
 *	
 *	For speed and simplicity the data that is being discarded by shortening the buffer is not actually deleted. If the new length is less than 0 or greater than the memory of the Teensy supports, nothing will change.
 *	
 *	@param val new length of the buffer.
 */
void T4setBufferSize(int32_t val);

/**	@brief Writes a value to the buffer.
 *	
 *	The buffer is cyclic, so older values will be overwritten.
 *	
 *	@param val Value to be written.
 */
void T4push(int32_t val);

/**	@brief Does nothing.
 */
void T4foo();

// Acess to individual bytes of an object (formerly at_macros)

/**	@brief Returns the least significant byte from a value @a v.
 *	
 *	The value is returned by masking.
 *	
 *	@param v Any numerical value
 */
#define LOWBYTE(v)     ((unsigned char) (v))

/**	@brief Returns the most significant byte from a 2B int value @a v.
 *	
 *	The value is returned by masking.
 *	
 *	@param v Any numerical 2B value
 */
#define HIGHBYTEINT(v) ((unsigned char) (((unsigned int) (v)) >> 8))

/**	@brief Returns the first significant byte from a 4B long value @a v.
 *	
 *	The value is returned by masking. The byte order is:
 *	Byte4 Byte3 Byte2 Byte1
 *	MSB               LSB
 *	3L    2L    1L    LOWBYTE
 *	
 *	@param v Any numerical 4B long value
 */
#define HIGHBYTE1L(v)  ((unsigned char) (((unsigned long) (v)) >> 8))

/**	@brief Returns the second significant byte from a 4B long value @a v.
 *	
 *	The value is returned by masking. The byte order is:
 *	Byte4 Byte3 Byte2 Byte1
 *	MSB               LSB
 *	3L    2L    1L    LOWBYTE
 *	
 *	@param v Any numerical 4B long value
 */
#define HIGHBYTE2L(v)  ((unsigned char) (((unsigned long) (v)) >> 16))

/**	@brief Returns the third significant byte from a 4B long value @a v.
 *	
 *	The value is returned by masking. The byte order is:
 *	Byte4 Byte3 Byte2 Byte1
 *	MSB               LSB
 *	3L    2L    1L    LOWBYTE
 *	
 *	@param v Any numerical 4B long value
 */
#define HIGHBYTE3L(v)  ((unsigned char) (((unsigned long) (v)) >> 24))

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

/**	@brief Read and write access to the low+4 byte.
 *	
 *	This macro relies on pointer arithmetic, so be sure
 *	the datatype is well defined!
 *	
 *	@param v Any numerical value. Make sure the value is as long as the requested byte!
 */
#define H4BYTE(v) (*((unsigned char*) (&v) + 4))

/**	@brief Read and write access to the low+5 byte.
 *	
 *	This macro relies on pointer arithmetic, so be sure
 *	the datatype is well defined!
 *	
 *	@param v Any numerical value. Make sure the value is as long as the requested byte!
 */
#define H5BYTE(v) (*((unsigned char*) (&v) + 5))

/**	@brief Read and write access to the low+6 byte.
 *	
 *	This macro relies on pointer arithmetic, so be sure
 *	the datatype is well defined!
 *	
 *	@param v Any numerical value. Make sure the value is as long as the requested byte!
 */
#define H6BYTE(v) (*((unsigned char*) (&v) + 6))

/**	@brief Read and write access to the low+7 byte.
 *	
 *	This macro relies on pointer arithmetic, so be sure
 *	the datatype is well defined!
 *	
 *	@param v Any numerical value. Make sure the value is as long as the requested byte!
 */
#define H7BYTE(v) (*((unsigned char*) (&v) + 7))

#endif
