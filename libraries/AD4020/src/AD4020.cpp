#include "AD4020.h"

#define NOP __asm__ __volatile__ ("nop\n\t" "nop\n\t")	/**< Idle for one processor cycle. */

#define settingSamplerate 0		/**< Setting for the samplerate. */
#define settingOversamples 1	/**< Setting for the number of oversamples. */
#define settingTimer 2			/**< Setting for the timer to be used for interrupt based operation. */
#define settingTiming 3			/**< Setting for using the timing pin. */
#define settingNoSkip 4			/**< Setting for cancelling the ISR. */
#define settingInvalid -1		/**< Invalid setting. */

// Variables for configuring reading the data
static uint32_t samplerate;				/**< Samplerate in Hz. */
static uint32_t oversamples = 1;		/**< Number of samples per data point. */
static uint32_t sampleCycle = 0;		/**< Current position in the oversampling cycle. */
static uint32_t readVal = 0;			/**< Current sum of values read. */
static float gainCorrection = 1.0;		/**< Correction factor for gain error (not implemented yet). */
static int32_t offsetCorrection = 0;	/**< Correction value for offset error. */

static const uint16_t regLen = 4*4096;	/**< Length of the data register in Bytes. */
static uint8_t register1[regLen];		/**< Data register 1. */
static uint8_t register2[regLen];		/**< Data register 2. */
static uint8_t register3[regLen];		/**< Data register 3. */
static int16_t posReg = 0;				/**< Position in the current data register to write to. */
static uint8_t writeReg = 0;			/**< Current data register to write to:
										 *   0 = register 1, 1 = register 2, 2 = register 3. */
static uint8_t readReg = 0;				/**< register to read and send data from to the PC:
										 *   0 = register 1, 1 = register 2, 2 = register 3. */
static uint8_t full = 0;				/**< Stores wether the register to be read is full. */
static uint8_t stop = 0;				/**< Stores wether the program has to be stopped. */
static uint8_t initial = 2;				/**< Stores wether the program is in the initializing phase. */
static uint8_t timerCounter;			/**< Stores the timer counter to be used. */
extern uint32_t ccRate;					/**< Frequency of the timer counter. */

static bool useTiming = false;		/**< Specifies whether the timing pin is used. */
static bool noSkipping = true;		/**< Specifies whether the ISR will be cancelled if data is being read too fast to be sent. */

// Pins
extern uint8_t TimerPin;	/**< Pin for measuring timing. */
extern uint8_t DebugPin;	/**< Pin for debug mode. */
extern uint8_t CNV_AD4020;	/**< CNV pin of the AD4020. */
extern uint8_t SCLK_AD4020;	/**< Serial clock pin of the AD4020. */
extern uint8_t MOSI_AD4020;	/**< MOSI pin of the AD4020. */
extern uint8_t MISO_AD4020;	/**< MISO pin of the AD4020. */

/** Initializes a timer counter with the interrupt function to read data
 *  
 *  @param compare Value the timer counter will trigger the interrupt at.
 *  @param timer Timer counter to be used: 0 (GPT1) oder 1 (GPT2).
 */
static void interSetup(uint32_t compare, uint8_t timer);

/** Interrupt service routine for reading and storing values.
 */
static void readISR();

/** Checks a string and returns the configurable variable it matches followed by a "=".
 *  
 *  If it does, that part of the string is removed to leave the value to set the variable to.
 *  
 *  @param a String to be checked.
 *  @return Variable that matches the string (encoded).
 */
static uint8_t checkParam(String a);

void AD4020initialize(uint32_t samplerate, uint32_t numOversamples, uint8_t timer, bool timing, bool noSkip){
	AD4020initialize(samplerate, numOversamples, timer);	// Initialize AD4020, set oversamples and interrupt
	useTiming = timing;										// Set useTiming
	noSkipping = noSkip;									// Set noSkipping
}

void AD4020initialize(uint32_t samplerate, uint32_t numOversamples, uint8_t timer) {
	AD4020initialize();						// Initialize AD4020
	oversamples = numOversamples;			// Set oversamples
	interSetup(ccRate/samplerate, timer);	// Initialize interrupt
}

void AD4020initialize(bool timing) {
	useTiming = timing;						// Set useTiming
	AD4020initialize();						// Initialize AD4020
}

void AD4020initialize() {
	digitalWriteFast(MOSI_AD4020, HIGH);	// Use the converter in 3-wire-mode (SDI of the AD4020 set to HIGH)
	digitalWriteFast(CNV_AD4020, HIGH);		// Start the first conversion
	delayMicroseconds(1);
	digitalWriteFast(CNV_AD4020, LOW);		// Read the first result and discard it
	delayMicroseconds(1);
	digitalWriteFast(CNV_AD4020, HIGH);		// Start the next conversion
}

void AD4020updateSamplerate(uint32_t samplerate) {
	noInterrupts();	// Deactivate interrupts
	switch(timerCounter) {
		case 0:	GPT1_OCR1 = ccRate/samplerate - 1;	// Wert des Counters für das Auslösen des Interrupts setzen
				break;
		case 1:	GPT2_OCR1 = ccRate/samplerate - 1;	// Wert des Counters für das Auslösen des Interrupts setzen
				break;
	}
	interrupts();	// Reactivate interrupts
}

void AD4020updateOversamples(uint32_t numOversamples) {
	oversamples = numOversamples;
}

void AD4020updateTimer(uint8_t timer) {
	noInterrupts();			// Deactivate interrupts
	timerCounter = timer;	// Set timer counter
	switch(timerCounter) {
		case 0:	attachInterruptVector(IRQ_GPT1, readISR);	// Set interrupt function
				NVIC_ENABLE_IRQ(IRQ_GPT1);					// Activate interrupt in the nested vector interrupt controller
				GPT1_OCR1 = ccRate/samplerate - 1;			// Set compare value for triggering the interrupt
				GPT2_IR &= 0xFFFFFFFE;						// Deactivate the other timer counter
				break;
		case 1:	attachInterruptVector(IRQ_GPT2, readISR);	// Set interrupt function
				NVIC_ENABLE_IRQ(IRQ_GPT2);					// Activate interrupt in the nested vector interrupt controller
				GPT2_OCR1 = ccRate/samplerate - 1;			// Set compare value for triggering the interrupt
				GPT1_IR &= 0xFFFFFFFE;						// Deactivate the other timer counter
				break;
	}
	interrupts();			// Reactivate interrupts
}

void AD4020updateTiming(bool timing) {
	useTiming = timing;
}

void AD4020updateNoSkip(bool noSkip) {
	noSkipping = noSkip;
}

bool AD4020checkUpdate(String a) {
	bool b = false;
	if(a.startsWith("AD4020.")) {
		a.remove(0, 7);
		switch(checkParam(a)) {
			case settingSamplerate:		a.remove(0, 11);
										AD4020updateSamplerate(a.toInt());
										b = true;
										break;
			case settingOversamples:	a.remove(0, 12);
										AD4020updateOversamples(a.toInt());
										b = true;
										break;
			case settingTimer:			a.remove(0, 6);
										AD4020updateTimer(a.toInt());
										b = true;
										break;
			case settingTiming:			a.remove(0, 7);
										if(a == "true") {
											AD4020updateTiming(true);
											b = true;
										}
										else if(a == "false") {
											AD4020updateTiming(false);
											b = true;
										}
			case settingNoSkip:			a.remove(0, 7);
										if(a == "true") {
											AD4020updateNoSkip(true);
											b = true;
										}
										else if(a == "false") {
											AD4020updateNoSkip(false);
											b = true;
										}
		}
	}
	return b;
}

uint8_t checkParam(String a) {
	if(a.startsWith("samplerate=")) {
		return settingSamplerate;
	}
	if(a.startsWith("oversamples=")) {
		return settingOversamples;
	}
	if(a.startsWith("timer=")) {
		return settingTimer;
	}
	if(a.startsWith("timing=")) {
		return settingTiming;
	}
	if(a.startsWith("noSkip=")) {
		return settingNoSkip;
	}
	return settingInvalid;
}

void AD4020update(uint32_t samplerate, uint32_t numOversamples, uint8_t timer, bool timing, bool noSkip) {
	if(useTiming) {digitalWriteFast(TimerPin, HIGH);}
	noInterrupts();					// Deactivate interrupts
	oversamples = numOversamples;	// Set oversamples
	timerCounter = timer;			// Set timer counter
	useTiming = timing;
	noSkipping = noSkip;
	
	switch(timerCounter) {
		case 0:	attachInterruptVector(IRQ_GPT1, readISR);	// Set interrupt function
				NVIC_ENABLE_IRQ(IRQ_GPT1);					// Activate interrupt in the nested vector interrupt controller
				GPT1_OCR1 = ccRate/samplerate - 1;			// Set compare value for triggering the interrupt
				GPT2_IR &= 0xFFFFFFFE;						// Deactivate the other timer counter
				break;
		case 1:	attachInterruptVector(IRQ_GPT2, readISR);	// Set interrupt function
				NVIC_ENABLE_IRQ(IRQ_GPT2);					// Activate interrupt in the nested vector interrupt controller
				GPT2_OCR1 = ccRate/samplerate - 1;			// Set compare value for triggering the interrupt
				GPT1_IR &= 0xFFFFFFFE;						// Deactivate the other timer counter
				break;
	}
	
	interrupts();					// Reactivate interrupts
	if(useTiming) {digitalWriteFast(TimerPin, LOW);}
}

void interSetup(uint32_t compare, uint8_t timer) {
	timerCounter = timer;	// Timer-Counter setzen
	switch(timer) {
		case 0:	attachInterruptVector(IRQ_GPT1, readISR);	// Interruptfunktion festlegen
				NVIC_ENABLE_IRQ(IRQ_GPT1);					// Interrupt in der Interruptcontroller Tabelle aktivieren
				GPT1_OCR1 = compare - 1;					// Wert des Counters für das Auslösen des Interrupts setzen
				break;
		case 1:	attachInterruptVector(IRQ_GPT2, readISR);	// Interruptfunktion festlegen
				NVIC_ENABLE_IRQ(IRQ_GPT2);					// Interrupt in der Interruptcontroller Tabelle aktivieren
				GPT2_OCR1 = compare - 1;					// Wert des Counters für das Auslösen des Interrupts setzen
				break;
	}
}

void readISR() {
	if(useTiming) {digitalWriteFast(TimerPin,HIGH);}	// Start timing
	digitalWriteFast(CNV_AD4020, LOW);		// Activate AD4020 as SPI device
	switch(timerCounter) {
		case 0:	//GPT1_SR |= 0x00000001;	// Reset interrupt in state register
				GPT1_SR = 0x00000001;		// Reset interrupt in state register (direct writing saves approximately 80 ns!)
				break;
		case 1:	//GPT2_SR |= 0x00000001;	// Reset interrupt in state register
				GPT2_SR = 0x00000001;		// Reset interrupt in state register (direct writing saves approximately 80 ns!)
				break;
	}
	
	int32_t val = 0;
	
	val += digitalReadFast(MISO_AD4020) << 19;  // Read first bit
	digitalWriteFast(SCLK_AD4020,HIGH);			// Set serial clock to HIGH
	NOP;
	for(int x = 18; x>=0;x--) {
		digitalWriteFast(SCLK_AD4020,LOW);			// Set serial clock to LOW
		NOP; NOP; NOP; NOP;	NOP; NOP; NOP;			// Idle for the cycle of the clock
		NOP; NOP; NOP; NOP;	NOP; NOP; NOP;
		digitalWriteFast(SCLK_AD4020,HIGH);			// Set serial clock to HIGH
		val += digitalReadFast(MISO_AD4020) << x;	// Read bit and add it to the value
	}
	digitalWriteFast(SCLK_AD4020,LOW);			// Set serial clock to LOW
	digitalWriteFast(CNV_AD4020, HIGH);			// Start the next conversion
	
	// Process negative values correctly
	if (val & 0b10000000000000000000){
		val += 0b11111111111100000000000000000000;
	}
	
	// Correct offset error
	val += offsetCorrection;
	// Correct gain error (currently no effect)
	double gCorrected = val * gainCorrection;
	
	readVal += val;	// Sum up the values
	sampleCycle++;	// Inceremet the number of samples taken
	// If all samples for a data point have been accumulated, the data is written to the buffer
	if (sampleCycle >= oversamples){
		switch (writeReg){
			case 0:	// Register 1
				register1[posReg] = LBYTE(readVal);		posReg++;
				register1[posReg] = HBYTE(readVal);		posReg++;
				register1[posReg] = H2BYTE(readVal);	posReg++;
				register1[posReg] = H3BYTE(readVal);	posReg++;
				break;
			
			case 1:	// Register 2
				register2[posReg] = LBYTE(readVal);		posReg++;
				register2[posReg] = HBYTE(readVal);		posReg++;
				register2[posReg] = H2BYTE(readVal);	posReg++;
				register2[posReg] = H3BYTE(readVal);	posReg++;
				break;
			case 2:	// Register 3
				register3[posReg] = LBYTE(readVal);		posReg++;
				register3[posReg] = HBYTE(readVal);		posReg++;
				register3[posReg] = H2BYTE(readVal);	posReg++;
				register3[posReg] = H3BYTE(readVal);	posReg++;
				break;
		}
		// Switch to the next register if the current one is full
		if (posReg >= regLen){
			uint8_t prev = writeReg;		// Caches the number of the current register
			writeReg = (writeReg + 1) % 3;	// Switch to the next register
			posReg = 0;						// Go to the start of the register
			full = 1;						// The last register is now ready to be read and sent to the PC
			// If noSkipping is active and the register to be written to has not been sent yet, an error message is displayed
			// and the program is terminated (this means that data is being read faster than it is possible to send it)
			if(noSkipping && writeReg == readReg){
				// If the program is still in the initializing phase, it waits for everything to get ready
				if (initial > 0){
					noInterrupts();
					AD4020sendDataToPC();
					initial--;
					interrupts();
					return;
				}
				Serial.println("Data is being read faster than it can be sent! Programm will terminate.");
				digitalWriteFast(DebugPin, HIGH);
				// deactivate interrupt
				switch(timerCounter) {
					case 0:	GPT1_IR ^= 0x00000001;
					case 1:	GPT2_IR ^= 0x00000001;
				}
			}
		}
		readVal = 0;
		sampleCycle = 0;
	}
	//while (GPT1_SR & 0x00000001);	// Wait for the interrupt register to be reset
									// (unnecessary because the ISR last long enough, this saves approxiamtely 120 ns!)
	if(useTiming) {digitalWriteFast(TimerPin, LOW);}	// End timing
}

// Read a value and return it
int32_t AD4020readValue() {
	if(useTiming) {digitalWriteFast(TimerPin, HIGH);}
	digitalWriteFast(CNV_AD4020, LOW);				// Activate AD4020 as SPI device
	NOP; NOP; NOP; NOP;								// Wait for the first bit to arrive
	int32_t val = 0;
	digitalWriteFast(SCLK_AD4020,HIGH);				// Set serial clock to HIGH
	val += digitalReadFast(MISO_AD4020) << 19;		// Read first bit
	NOP;
	for(int x = 18; x>=0;x--) {
		digitalWriteFast(SCLK_AD4020,LOW);			// Set serial clock to LOW
		NOP; NOP; NOP; NOP;	NOP; NOP; NOP;			// Idle for the cycle of the clock
		NOP; NOP; NOP; NOP;	NOP; NOP; NOP;
		digitalWriteFast(SCLK_AD4020,HIGH);			// Set serial clock to HIGH
		val += digitalReadFast(MISO_AD4020) << x;	// Read bit and add it to the value
	}
	digitalWriteFast(SCLK_AD4020,LOW);           	// Set serial clock to LOW
	digitalWriteFast(CNV_AD4020, HIGH);				// Start the next conversion
	
	// Process negative values correctly
	if (val & 0b10000000000000000000){
		val += 0b11111111111100000000000000000000;
	}
	
	// Correct offset error
	val += offsetCorrection;
	// Correct gain error (currently no effect)
	double gCorrected = val * gainCorrection;
	
	if(useTiming) {digitalWriteFast(TimerPin, LOW);}
	return val;
}

void AD4020sendDataToPC() {
	if(!full) {return;}	// If the register isn't full yet, nothing happens
	if(useTiming) {digitalWriteFast(TimerPin, HIGH);}	// Start timing
	switch(readReg) {
		case 0:
			Serial.write(register1, regLen);
			break;
		case 1:
			Serial.write(register2, regLen);
			break;
		case 2:
			Serial.write(register3, regLen);
			break;
	}
	full = 0;
	readReg = (readReg + 1) % 3;
	if(useTiming) {digitalWriteFast(TimerPin, LOW);}	// End timing
}
