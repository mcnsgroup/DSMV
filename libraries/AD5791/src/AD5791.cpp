#include "AD5791.h"

#define NOP __asm__ __volatile__ ("nop\n\t" "nop\n\t")	/**< 2^0 Prozessortakte verschwenden. */

// Constants
#define dacWrite 0b0001 << 20					/**< Write to the DAC register. */
#define ctrlWrite 0b0010 << 20					/**< Write to the control register. */
#define dacRead 0b1001 << 20					/**< Read the value of the DAC register. */
#define ctrlRead 0b1010 << 20					/**< Read the value of the control register. */
#define clearCode 0b0011 << 20					/**< Register for the default output value of the AD5791. */
#define linComp 0b11 << 8						/**< Input range (Vref) up to 10V. */
#define opgnd 1 << 2							/**< Clamp output of the AD5791 to GND. */
#define dactri 1 << 3							/**< Deactivate regular operating mode. */
//#define outAmp 0b10							/**< Gain of one (output voltage from 0V to 10V on the DSMV board). */
#define outAmp 0								/**< Gain of two (output voltage from -10V bis 10V on the DSMV board). */
#define ZERO (1 << 18) - 1						/**< Value for a output voltage of 0V in regular operating mode. */
#define MAX (1 << 19) - 1						/**< Value for maximum output voltage in regular operating mode. */
#define stdCtrl (ctrlWrite | linComp | outAmp)	/**< Set the AD5791 to regular operating mode. */
#define INIT (clearCode | ZERO)					/**< Set the default output value to 0V. */
#define DAC0 (dacWrite | ZERO)					/**< Set the DAC output value to 0V. */
#define noOutput (ctrlWrite | opgnd | dactri)	/**< Control word to clamp output of the AD5791 to GND. */

// Command codes
#define settingVoltage 0		/**< Setting for the output voltage. */
#define settingDefaultVoltage 1	/**< Setting for the default voltage. */
#define commandStd 2			/**< Command for setting the AD5791 to regular operating mode. */
#define commandClear 3			/**< Command for setting the output to the default voltage. */
#define commandOff 4			/**< Command for clamping the output of the AD5791 to GND. */
#define invalid -1				/**< Invalid command. */

// Pins
extern uint8_t TimerPin;		/**< Pin for measuring timing. */
extern uint8_t SYNC_AD5791;		/**< SYNC pin of the AD5791. */
extern uint8_t RESET_AD5791;	/**< RESET pin of the AD5791. */
extern uint8_t CLR_AD5791;		/**< CLR pin of the AD5791. */
extern uint8_t LDAC_AD5791;		/**< LDAC pin of the AD5791. */
extern uint8_t SCLK_AD5791;		/**< SCLK pin of the AD5791. */
extern uint8_t MOSI_AD5791;		/**< MOSI pin of the AD5791. */

static float minVoltage = 0;	/**< Stores the minimum output voltage (V). */
static float maxVoltage = 0;	/**< Stores the maximum output voltage (V). */
static float outputRange = 0;	/**< Stores the range of the output voltage. */

/** Checks a string and returns the configurable variable it matches followed by a "=" or a command.
 *  
 *  If it does, that part of the string is removed to leave the value to set the variable to (if it was a variable).
 *  
 *  @param a String to be checked.
 *  @return Variable that matches the string (encoded).
 */
static uint8_t checkParam(String a);

void AD5791initialize(float minV, float maxV) {
	minVoltage = minV;						// Set the minimum output voltage
	maxVoltage = maxV;						// Set the maximum output voltage
	outputRange = maxV - minV;				// Set the range of the output voltage
	delayMicroseconds(20000);
	digitalWriteFast(RESET_AD5791, HIGH);	// Wake AD5791 from reset mode
	delayMicroseconds(20);

	digitalWriteFast(SYNC_AD5791, HIGH);	// Set the SYNC pin to HIGH for the first output voltage
	delayMicroseconds(10);

	AD5791regWrite(INIT);	// Set clearcode register
	AD5791regWrite(DAC0);	// Set DAC register
	AD5791clearOutput();	// AD5791 now outputs the default voltage
	AD5791standardMode();	// Set the AD5791 to regular operation mode
	delayMicroseconds(1000);
}

void AD5791standardMode() {
	AD5791regWrite(stdCtrl);
}

void AD5791clearOutput() {
	digitalWriteFast(CLR_AD5791, LOW);
	delayMicroseconds(10);
	digitalWriteFast(CLR_AD5791, HIGH);
}

/**	@brief Checks wether a given voltage lies in the boundaries and possibly corrects it.
 *	
 *	@param voltage Voltage to be checked (V).
 *	@return Input voltage after adjusting according to limits.
 */
float checkVoltage(float voltage) {
	if(voltage > maxVoltage) {
		voltage = maxVoltage;
	}
	else if(voltage < minVoltage) {
		voltage = minVoltage;
	}
	return voltage;
}

void AD5791setDefaultVoltage(float defaultVoltage) {
	// Check input voltage and possibly corrects it.
	defaultVoltage = checkVoltage(defaultVoltage);
	// Convert voltage value into SPI code
	uint32_t value = clearCode | (uint32_t) ((defaultVoltage - minVoltage)*((1 << 19) - 1)/outputRange);
	// Write code to the AD5791
	AD5791regWrite(value);
}

void AD5791off() {
	AD5791regWrite(noOutput);
}

void AD5791regWrite(uint32_t data) {
	digitalWriteFast(SYNC_AD5791, LOW);		// Set SYNC pin to LOW
	uint8_t byte1 = H2BYTE(data);
	uint8_t byte2 = HBYTE(data);
	uint8_t byte3 = LBYTE(data);
	AD5791sendSPI(byte1);
	AD5791sendSPI(byte2);
	AD5791sendSPI(byte3);
	digitalWriteFast(SYNC_AD5791, HIGH);   // Set SYNC pin back to HIGH
	digitalWriteFast(LDAC_AD5791, LOW);    // DAC is now being updated
	NOP; NOP; NOP; NOP; NOP; NOP;
	digitalWriteFast(LDAC_AD5791, HIGH);   // Set LDAC pin back to HIGH
}

void AD5791setVoltage(float voltage) {
	// Check input voltage and possibly corrects it.
	voltage = checkVoltage(voltage);
	// Convert voltage value into SPI code
	uint32_t value = dacWrite | (uint32_t) ((voltage - minVoltage)*((1 << 19) - 1)/outputRange);
	// Write code to the AD5791
	AD5791regWrite(value);
}

void AD5791sendSPI(uint8_t byte) {
	for(int i = 7; i >= 0; i--) {
		digitalWriteFast(SCLK_AD5791, LOW);				// Set the clock signal (back) to LOW
		NOP;											// Wait for the clock signal to reach LOW state
		digitalWriteFast(MOSI_AD5791, (byte >> i) % 2);	// Set the respective bit on the MOSI
		digitalWriteFast(SCLK_AD5791, HIGH);			// Clock in the return bit (rising edge)
		NOP; NOP;										// Idle for the cycle of the clock
	}
	digitalWriteFast(SCLK_AD5791, LOW);					// Set the clock signal (back) to LOW
}

bool AD5791checkUpdate(String a) {
	bool b = false;
	if(a.startsWith("AD5791.")) {
		b = true;
		a.remove(0, 7);
		switch(checkParam(a)) {
			case settingVoltage:		a.remove(0, 8);
										AD5791setVoltage(a.toFloat());
										break;
			case settingDefaultVoltage:	a.remove(0, 15);
										AD5791setDefaultVoltage(a.toFloat());
										AD5791clearOutput();
										break;
			case commandStd:			AD5791standardMode();
										break;
			case commandClear:			AD5791clearOutput();
										break;
			case commandOff:			AD5791off();
										break;
		}
	}
	return b;
}

uint8_t checkParam(String a) {
	if(a.startsWith("voltage=")) {
		return settingVoltage;
	}
	if(a.startsWith("defaultVoltage=")) {
		return settingDefaultVoltage;
	}
	if(a.startsWith("standard")) {
		return commandStd;
	}
	if(a.startsWith("default")) {
		return commandClear;
	}
	if(a.startsWith("off")) {
		return commandOff;
	}
	return invalid;
}
