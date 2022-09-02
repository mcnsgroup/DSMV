#include "LTC2500.h"

#define NOP __asm__ __volatile__ ("nop\n\t" "nop\n\t")	/**< Idle for one processor cycle. */

#define settingSamplerate 0			/**< Setting for the samplerate. */
#define settingOversamples 1		/**< Setting for the number of oversamples. */
#define settingTimer 2				/**< Setting for the timer to be used for interrupt based operation. */
#define settingTiming 3				/**< Setting for using the timing pin. */
#define settingNoSkip 4				/**< Setting for cancelling the ISR. */
#define settingOutputMode 5			/**< Setting for the output mode. */
#define settingInvalid -1			/**< Invalid setting. */
#define controlWord 0b100000000000	/**< Control word for configuring the internal filter. */

// Preprocessor instructions to take the board version into account (exrta delay in signals due to ADUMS since version 1.1)
#if BOARD_VERSION >= 11
#define idle1 NOP; NOP; NOP; NOP; NOP; NOP; NOP; NOP; NOP; NOP; NOP; NOP; NOP; NOP
#define idle2
#else
#define idle1 NOP; NOP; NOP; NOP; NOP; NOP
#define idle2 NOP; NOP; NOP; NOP
#endif

// Variables for configuring reading the data
static uint32_t samplerate = 0;			/**< Samplerate in Hz. */
static uint32_t oversamples = 1;		/**< Number of samples per data point. */
static uint32_t sampleCycle = 0;		/**< Current position in the oversampling cycle. */
static int32_t readVal = 0;				/**< Current sum of values read. */
static float gainCorrection = 1.0;		/**< Correction factor for gain error (not implemented yet). */
static int32_t offsetCorrection = 0;	/**< Correction value for offset error. */

static const uint16_t regLen = 4*4096;			/**< Length of the data register in Bytes. */
static uint8_t register1[regLen];				/**< Data register 1. */
static uint8_t register2[regLen];				/**< Data register 2. */
static uint8_t register3[regLen];				/**< Data register 3. */
static int16_t posReg = 0;						/**< Position in the current data register to write to. */
static uint8_t writeReg = 0;					/**< Current data register to write to:
												 *   0 = register 1, 1 = register 2, 2 = register 3. */
static uint8_t readReg = 0;						/**< register to read and send data from to the PC:
												 *   0 = register 1, 1 = register 2, 2 = register 3. */
static uint8_t full = 0;						/**< Stores wether the register to be read is full. */
static uint8_t stop = 0;						/**< Stores wether the program has to be stopped. */
static uint8_t initial = 2;						/**< Stores wether the program is in the initializing phase. */
static uint8_t outputMode = noLatencyOutput;	/**< Stores which output sends data via the SPI bus (SDOA by default). */
static uint8_t timerCounter;					/**< Stores the timer counter to be used. */
extern uint32_t ccRate;							/**< Frequency of the timer counter. */

static bool useTiming = false;		/**< Specifies whether or not the timing pin is used. */
static bool noSkipping = true;		/**< Specifies whether or not the ISR will be cancelled if data is being read too fast to be sent. */

// Pins
extern uint8_t TimerPin;		/**< Pin for measuring timing. */
extern uint8_t DebugPin;		/**< Pin for debug mode. */
extern uint8_t MCLK_LTC2500;	/**< MCLK pin of the LTC2500. */
extern uint8_t RDLA_LTC2500;	/**< RDLA pin of the LTC2500. */
extern uint8_t RDLB_LTC2500;	/**< RDLB pin of the LTC2500. */
extern uint8_t PRE_LTC2500;		/**< PRE pin of the LTC2500. */
extern uint8_t DRL_LTC2500;		/**< DRL pin of the LTC2500. */
extern uint8_t BUSY_LTC2500;	/**< BUSY indicator of the LTC2500. */
extern uint8_t SCLK_LTC2500;	/**< Serial clock of the LTC2500. */
extern uint8_t MOSI_LTC2500;	/**< MOSI pin of the LTC2500. */
extern uint8_t MISO_LTC2500;	/**< MISO pin of the LTC2500. */

/** Initializes a timer counter with the interrupt function to read data
 *  
 *  @param compare Value the timer counter will trigger the interrupt at.
 *  @param timer Timer counter to be used: 0 (GPT1) oder 1 (GPT2).
 */
static void interSetup(uint8_t timer);

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

void LTC2500initialize(uint32_t srate, uint32_t numOversamples, uint8_t timer, uint8_t mode, bool timing, bool noSkip) {
	digitalWriteFast(MOSI_LTC2500, HIGH);	// Silence the data input
	samplerate = srate;						// Set samplerate
	oversamples = numOversamples;			// Set oversamples
	interSetup(timer);						// Initialize interrupt
	LTC2500updateOutputMode(mode);			// Set output mode
	useTiming = timing;						// Set useTiming
	noSkipping = noSkip;					// Set noSkipping
}

void LTC2500initialize(uint32_t srate, uint32_t numOversamples, uint8_t timer, uint8_t mode) {
	LTC2500initialize(srate, numOversamples, timer, mode, false, true);
}

void LTC2500initialize(uint8_t mode, bool timing) {
	digitalWriteFast(MOSI_LTC2500, HIGH);	// Silence the data input
	LTC2500updateOutputMode(mode);			// Set output mode
	useTiming = timing;						// Set useTiming
}

void LTC2500initialize() {
	digitalWriteFast(MOSI_LTC2500, HIGH);		// Silence the data input
	LTC2500updateOutputMode(noLatencyOutput);	// Set output mode
}

bool LTC2500checkUpdate(String a) {
	bool b = false;
	if(a.startsWith("LTC2500.")) {
		b = true;
		a.remove(0, 8);
		switch(checkParam(a)) {
			case settingSamplerate:		a.remove(0, 11);
										LTC2500updateSamplerate(a.toInt());
										break;
			case settingOversamples:	a.remove(0, 12);
										LTC2500updateOversamples(a.toInt());
										break;
			case settingTimer:			a.remove(0, 6);
										LTC2500updateTimer(a.toInt());
										break;
			case settingOutputMode:		a.remove(0, 11);
										LTC2500updateOutputMode(a.toInt());
										break;
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
	if(a.startsWith("outputMode=")) {
		return settingOutputMode;
	}
	return settingInvalid;
}

void LTC2500update(uint32_t srate, uint32_t numOversamples, uint8_t timer, uint8_t mode) {
	LTC2500updateSamplerate(srate);
	LTC2500updateOversamples(numOversamples);
	LTC2500updateTimer(timer);
	LTC2500updateOutputMode(mode);
}

void LTC2500updateSamplerate(uint32_t srate) {
	noInterrupts();	// Deactivate interrupts
	samplerate = srate;	// Update samplerate
	switch(timerCounter) {
		case 0:	GPT1_OCR1 = ccRate/samplerate - 1;	// Set compare value for triggering the interrupt
				break;
		case 1:	GPT2_OCR1 = ccRate/samplerate - 1;	// Set compare value for triggering the interrupt
				break;
	}
	interrupts();	// Reactivate interrupts
}

void LTC2500updateOversamples(uint32_t numOversamples) {
	oversamples = numOversamples;
}

void LTC2500updateTimer(uint32_t timer) {
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

void LTC2500updateOutputMode(uint8_t mode) {
	// Update outputMode unless the output is being silenced
	if(mode == noLatencyOutput || mode == filteredOutput) {
		outputMode = mode;
	}
	switch(mode) {
		case noLatencyOutput:	digitalWriteFast(RDLA_LTC2500, HIGH);	// Set SDOA to high impedance
								digitalWriteFast(RDLB_LTC2500, LOW);	// SDOB may send data
								digitalWriteFast(PRE_LTC2500, LOW);		// Deactivate averaging filter
								break;
		case filteredOutput:	digitalWriteFast(RDLA_LTC2500, LOW);	// SDOA may send data
								digitalWriteFast(RDLB_LTC2500, HIGH);	// Set SDOB to high impedance
								digitalWriteFast(PRE_LTC2500, HIGH);	// Activate averaging filter
								break;
		case silent:			digitalWriteFast(RDLA_LTC2500, HIGH);	// Set SDOA to high impedance
								digitalWriteFast(RDLB_LTC2500, HIGH);	// Set SDOB to high impedance
								break;
	}
}

void interSetup(uint8_t timer) {
	noInterrupts();			// Deactivate interrupts
	timerCounter = timer;	// Set timer counter
	switch(timerCounter) {
		case 0:	attachInterruptVector(IRQ_GPT1, readISR);	// Set interrupt function
				NVIC_ENABLE_IRQ(IRQ_GPT1);					// Activate interrupt in the nested vector interrupt controller
				GPT1_OCR1 = ccRate/samplerate - 1;			// Set compare value for triggering the interrupt
				break;
		case 1:	attachInterruptVector(IRQ_GPT2, readISR);	// Set interrupt function
				NVIC_ENABLE_IRQ(IRQ_GPT2);					// Activate interrupt in the nested vector interrupt controller
				GPT2_OCR1 = ccRate/samplerate - 1;			// Set compare value for triggering the interrupt
				break;
	}
	interrupts();			// Reactivate interrupts
}

void readISR() {
	if(useTiming) {digitalWriteFast(TimerPin, HIGH);}	// Start timing
	digitalWriteFast(MCLK_LTC2500, LOW);	// Activate LTC2500 as SPI device
	switch(timerCounter) {
		case 0:	//GPT1_SR |= 0x00000001;	// Reset interrupt in state register
				GPT1_SR = 0x00000001;		// Reset interrupt in state register (direct writing saves approximately 80 ns!)
				break;
		case 1:	//GPT2_SR |= 0x00000001;	// Reset interrupt in state register
				GPT2_SR = 0x00000001;		// Reset interrupt in state register (direct writing saves approximately 80 ns!)
				break;
	}
	
	// Variant: averaging-Filter of the LTC2500 for oversampling
	if(outputMode == filteredOutput) {
		if(sampleCycle < oversamples - 1) {
			sampleCycle++;							// Inceremet the number of samples taken
			while (GPT1_SR & 0x00000001);			// Wait for the interrupt register to be reset
			NOP; NOP; NOP; NOP; NOP; NOP; NOP; NOP;	// Give the LTC2500 time to process the data
			NOP; NOP; NOP; NOP; NOP; NOP; NOP; NOP;
			NOP; NOP; NOP; NOP; NOP; NOP; NOP; NOP;
			NOP; NOP; NOP; NOP; NOP; NOP; NOP; NOP;
			NOP; NOP; NOP; NOP; NOP; NOP; NOP; NOP;
			NOP; NOP; NOP; NOP; NOP; NOP; NOP; NOP;
			NOP; NOP; NOP;
			digitalWriteFast(MCLK_LTC2500, HIGH);	// Initiate the next conversion
			
			return;
		}
	}
	
	int32_t val = 0;
	
	while(digitalRead(BUSY_LTC2500));	// Wait until the LTC2500 is ready
	
	// If using the filtered output, the first bit is immediately available to read
	if(outputMode == filteredOutput) {
		val += digitalReadFast(MISO_LTC2500) << 31;
		// Clock in the bits
		for (int x = 30; x >= 0; x--){
			digitalWriteFast(SCLK_LTC2500, HIGH);
			idle1;
			/*NOP; NOP; NOP; NOP; NOP; NOP; NOP;
			NOP; NOP; NOP; NOP; NOP; NOP; NOP;*/
			digitalWriteFast(SCLK_LTC2500, LOW);
			idle2;
			val += digitalReadFast(MISO_LTC2500) << x;
		}
	}
	else{
		// Clock in the bits
		for (int x = 23; x >= 0; x--){
			digitalWriteFast(SCLK_LTC2500, HIGH);
			idle1;
			//NOP; NOP; NOP; NOP; NOP; NOP;
			/*NOP; NOP; NOP; NOP; NOP; NOP; NOP;
			NOP; NOP; NOP; NOP; NOP; NOP; NOP;*/
			digitalWriteFast(SCLK_LTC2500, LOW);
			//NOP; NOP; NOP; NOP;
			idle2;
			val += digitalReadFast(MISO_LTC2500) << x;
		}
	}
	
	digitalWriteFast(MCLK_LTC2500, HIGH);	// Initiate the next conversion
	
	// Process negative values correctly
	if (outputMode == noLatencyOutput && (val & 0b100000000000000000000000)){
		val += 0b11111111000000000000000000000000;
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
			// and the program is terminated (this means that data iis being read faster than it is possible to send it)
			if(noSkipping && writeReg == readReg){
				// If the program is still in the initializing phase, it waits for everything to get ready
				if (initial > 0){
					noInterrupts();
					LTC2500sendDataToPC();
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
	if(useTiming) {digitalWriteFast(TimerPin, LOW);}	// End timing
}

int32_t LTC2500readValue() {
	if(useTiming) {digitalWriteFast(TimerPin, HIGH);}	// Start timing
	digitalWriteFast(MCLK_LTC2500, HIGH);	// Initiate the conversion
	digitalWriteFast(MCLK_LTC2500, LOW);
	LTC2500updateOutputMode(outputMode);	// Activate LTC2500 as SPI device in case it was silent
	int32_t val = 0;
	while(digitalRead(BUSY_LTC2500));		// Wait until the LTC2500 is ready
	
	// If using the filtered output, the first bit is immediately available to read
	if(outputMode == filteredOutput) {
		val += digitalReadFast(MISO_LTC2500) << 31;
		// Clock in the bits
		for (int x = 30; x >= 0; x--){
			digitalWriteFast(SCLK_LTC2500, HIGH);
			idle1;
			/*NOP; NOP; NOP; NOP; NOP; NOP; NOP;
			NOP; NOP; NOP; NOP; NOP; NOP; NOP;*/
			digitalWriteFast(SCLK_LTC2500, LOW);
			idle2;
			val += digitalReadFast(MISO_LTC2500) << x;
		}
	}
	else{
		// Clock in the bits
		for (int x = 23; x >= 0; x--){
			digitalWriteFast(SCLK_LTC2500, HIGH);
			idle1;
			//NOP; NOP; NOP; NOP; NOP; NOP;
			/*NOP; NOP; NOP; NOP; NOP; NOP; NOP;
			NOP; NOP; NOP; NOP; NOP; NOP; NOP;*/
			digitalWriteFast(SCLK_LTC2500, LOW);
			//NOP; NOP; NOP; NOP;
			idle2;
			val += digitalReadFast(MISO_LTC2500) << x;
		}
	}
	
	LTC2500updateOutputMode(silent);	// Silence the LTC2500 output
	
	// Process negative values correctly
	if (outputMode == noLatencyOutput && (val & 0b100000000000000000000000)){
		val += 0b11111111000000000000000000000000;
	}
	
	// Correct offset error
	val += offsetCorrection;
	// Correct gain error (currently no effect)
	double gCorrected = val * gainCorrection;
	
	if(useTiming) {digitalWriteFast(TimerPin, LOW);}	// End timing
	return val;
}

void LTC2500sendDataToPC() {
	if (!full){return;}	// If the register isn't full yet, nothing happens
	if(useTiming) {digitalWriteFast(TimerPin, HIGH);}	// Start timing
	switch (readReg){
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

void LTC2500configureFilter(int type, int downsampling, bool DGE, bool DGC) {
	uint16_t command = controlWord;	// All modifiers will be added to the basic control word.
	// Check the filter type
	if (type < 1 || type > 7) {
		return;
	}
	command += type;	// Add the filter type
	// Check the downsampling exponent
	if(downsampling < 2 || downsampling > 14) {
		return;
	}
	// Add the downsampling exponent
	command += downsampling << 4;
	// Add the DGE switch
	command += DGE << 8;
	// Add the DGC switch
	command += DGC << 9;
	// Send the full command to the LTC2500
	LTC2500sendCommand(command);
}

void LTC2500sendCommand(int command) {
	// Pin toggling to start the transaction
	digitalWriteFast(DRL_LTC2500, HIGH);
	NOP; NOP; NOP; NOP; NOP; NOP;
	digitalWriteFast(MCLK_LTC2500, LOW);
	NOP; NOP; NOP; NOP; NOP; NOP;
	digitalWriteFast(DRL_LTC2500, LOW);
	
	for(int x = 11; x >= 0; x--) {
		digitalWriteFast(MOSI_LTC2500, (command >> x) % 2);
		digitalWriteFast(SCLK_LTC2500, HIGH);
		NOP; NOP; NOP; NOP; NOP; NOP;
		digitalWriteFast(SCLK_LTC2500, LOW);
	}
	// Reset the Pins
	digitalWriteFast(MOSI_LTC2500, LOW);
	digitalWriteFast(MCLK_LTC2500, HIGH);
}
