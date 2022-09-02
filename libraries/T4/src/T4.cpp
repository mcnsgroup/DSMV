#include "T4.h"

// Internal elements

static int pins[T4maxPin];								/**< Stores the output pins. */
static int pwmRes = 1 << 8;								/**< Resolution of the PWM-output (standard 9 Bit). */
static int arRes = 1 << 9;								/**< Resolution of the analog inputs (standard 10 Bit). */
static void (*in1)();									/**< Pointer for the interrupt service routine of GPT1. */
static void (*in2)();									/**< Pointer for the interrupt service routine of GPT2. */
static volatile uint64_t timer = 0;						/**< Time since program start (µs). */
static volatile uint32_t timerRefreshed = 0;			/**< Stores the value of the GPT1 when refreshing the timer. */
static uint8_t GPT1InUse = false;						/**< Stores whether GPT1 has an active ISR. */
static uint8_t GPT2InUse = false;						/**< Stores whether GPT2 has an active ISR. */
static bool (*serialFuncs[T4maxSerialFuncs])(String a);	/**< Array for the functions, that are executed to check the serial buffer. */
static uint8_t numSerialFuncs = 0;						/**< Current number of functions to check the serial buffer. */
static bool checkingBuffer = false;						/**< Flag that indicates whether the serial buffer is being checked currently. */
static bool newCommand = false;							/**< Flag that indicates whether there is a new command in the serial buffer to be checked. */

// Signal generator
static const int maxSignals = 4;	/**< Maximum number of singular signals (limited by the memory of the Teensy). */
static uint16_t numSignals = 0;		/**< Current number of singular signals. */
static float sig[maxSignals][3];	/**< Array to store the parameters of the singular signals.
									 *   Index 1 = signal number, Index 2 = signal parameters:
									 *   sig[...][0] = frequency, sig[...][1] = amplitude, sig[...][2] = phase. */
static float freqCarrier = 0;		/**< Carrier frequency of the FM signal. */
static float ampCarrier = 0;		/**< Amplitude of the FM signal. */
static float freqModulation = 0;	/**< Bandwidth of the frequency modulation. */
static float ampModulation = 0;		/**< Deprecated. */

static const int bufferLen = 100;			/**< Maximum number of characters in the serial buffer. */
static char serialBuffer[bufferLen + 1];	/**< Ring buffer for reading the serial interface. */
static int bufferPos = 0;					/**< Current position in the serial buffer. */

void T4setInterrupt1(void (*func)()) {
	in1 = func;
}

void T4setInterrupt2(void (*func)()) {
	in2 = func;
}

// Pins
extern uint8_t T4mosi;		/**< MOSI pin for SPI communication. */
extern uint8_t T4miso;		/**< MISO pin for SPI communication. */
extern uint8_t T4sclk;		/**< Clock pin for SPI communication. */
extern uint8_t SucessPin;	/**< Pin for measuring timing and displaying a succesful processing of a command. */
extern uint8_t FailPin;		/**< Pin for debugging and displaying a failed processing of a command. */

/**< @brief Duration of the pulse to indicate a successful (or unsuccessful) processing of the serial buffer in ms. */
int pulseTime = 0;
int T4sigLen = T4maxSigLen;
float T4sig[T4maxSigLen];
uint8_t T4pulse[T4maxSigLen];

void T4pinSetup(const int outPins[], int size) {
  for(int i = 0; i < size; i++) {
    pinMode(outPins[i], OUTPUT);
	T4pln(outPins[i]);
    pins[i] = outPins[i];
  }
}

void T4awr(int res) {
	// Check for invalid value (too great or small) and possibly correct
	if(res < 1) {
		res = 1;
	}
	else if(res > 12) {
		res = 12;
	}
	analogWriteResolution(res);	// Set bit resolution
	pwmRes = 1 << res;			// Update resolution variable
}

void T4awV(int pin, float voltage) {
	// Check for invalid value (too great or small) and possibly correct
	if(voltage > 3.3) {
		voltage = 3.3;
	}
	else if(voltage < 0) {
		voltage = 0;
	}

	uint32_t value = (voltage * pwmRes - 1) / 3.3;	// Convert voltage into a value for the analog output
	T4aw(pin, value);								// Set value
}

void T4arr(int res) {
	// The Teensy 4.0 can only differentiate 10 Bit and 12 Bit
	if(res != 10) {
		res = 12;
	}
	analogReadResolution(res);	// Set bit resolution
	arRes = 1 << (res - 1);		// Update resolution variable
}

void T4aravg(int samples) {
	analogReadAveraging(samples);	// Set bit resolution
}

float T4arV(int pin) {
	int32_t val = T4ar(pin);						// Read value
	val -= arRes;									// Shift value into the correct range
	float voltage = val * 3.3 / ((arRes << 1) - 1);	// Convert value to actual voltage
	return voltage;
}

void T4dw(int pin, int value) {
  digitalWriteFast(pin, value);
}

void T4aw(int pin, int value) {
	analogWrite(pin, value);
}

int T4dr(int pin) {
  return digitalReadFast(pin);
}

int T4ar(int pin) {
	return analogRead(pin);
}

void T4toggle(int pin) {
  T4dw(pin, !T4dr(pin));
}

void T4stop() {
  for(int i = 0; i <= T4maxPin; i++) {
    T4dw(i, LOW);
    pinMode(i, INPUT);
  }
  Serial.end();
  exit(0);
}

uint8_t T4SPIsend(uint8_t byte, uint8_t clkSpeed) {
	uint8_t readByte = 0;								// Value to be read
	for(int i = 0; i <= 7; i++) {
		digitalWriteFast(T4mosi, (byte >> i) % 2);		// Set the respective bit on the MOSI
		NOP5;											// Idle until bit is set
		digitalWriteFast(T4sclk, HIGH);					// Clock in the return bit (rising edge)
		NOP5;											// Idle for the cycle of the clock
		digitalWriteFast(T4sclk, LOW);					// Set clock signal to LOW
		readByte += digitalReadFast(T4miso) << (7 - i);	// Read bit and add it to return value
	}
	return readByte;
}

void T4SPIsendFast(uint8_t byte, uint8_t clkSpeed) {
	for(int i = 7; i >= 0; i--) {
		digitalWriteFast(T4sclk, LOW);				// Set clock (back) to LOW
		NOP0;										// Wait for clock signal to reach LOW state
		digitalWriteFast(T4mosi, (byte >> i) % 2);	// Set the respective bit on the MOSI
		digitalWriteFast(T4sclk, HIGH);				// Set clock signal to HIGH
		NOP1;										// Idle for the cycle of the clock
	}
	digitalWriteFast(T4sclk, LOW);					// Set clock signal to LOW
}

uint8_t T4SPIread(uint8_t clkSpeed) {
	uint8_t readByte = 0;								// Value to be read
	for(int i = 0; i <= 7; i++) {
		digitalWriteFast(T4sclk, HIGH);					// Clock in the bit (rising edge)
		NOP5;											// Idle for the cycle of the clock
		digitalWriteFast(T4sclk, LOW);					// Set clock signal to LOW
		readByte += digitalReadFast(T4miso) << (7 - i);	// Read bit and add it to return value
	}
	return readByte;
}

double T4getTime() {
	uint32_t counter = GPT1_CNT;					// Read value of the GPT1
	return (double) (timer + counter) / T4ccRate;	// return time in seconds
}

void T4addSignal(float freq, float amp, float ph) {
  if(numSignals < maxSignals) { // Checks wether the is enough capacity for an additional signal
    sig[numSignals][0] = freq;  // Store frequency
    sig[numSignals][1] = amp;   // Store amplitude
    sig[numSignals][2] = ph;    // Store phase
    numSignals++;
  }
}

void T4clearSignal() {
  numSignals = 0;
}

double T4sigValue() {
	double t = T4getTime();	// Get the current time
	double value = 0;		// Value for the voltage
	for(int i = 0; i < numSignals; i++) {
		value += sig[i][1] * cos(2 * PI * sig[i][0] * t - sig[i][2]);	// Combine all signals
	}
	return value;
}

double T4sigValue(double t) {
	double value = 0; // Value for the voltage
	for(int i = 0; i < numSignals; i++) {
		value += sig[i][1] * cos(2 * PI * sig[i][0] * t - sig[i][2]);	// Combine all signals
	}
	return value;
}

void T4sigTable(float values[], float amp) {
	for(int i = 0; i < min(T4sigLen, T4maxSigLen); i++) {
		values[i] = amp * sin((i*2*PI) / T4sigLen + PI/2);
	}
}

void T4sigTable(float values[]) {
	T4sigTable(values, 1);
}

void T4pulseTable(uint8_t values[]) {
	for(int i = 0; i < min(T4sigLen, T4maxSigLen); i++) {
		if(sin((i*2*PI) / T4sigLen + PI/2) > 0) {
			values[i] = HIGH;
		}
		else {
			values[i] = LOW;
		}
	}
}

void T4setFM(float freqC, float ampC, float freqM, float ampM) {
	freqCarrier = freqC;	// Set carrier frequency
	ampCarrier = ampC;		// Set carrier amplitude
	freqModulation = freqM;	// Set modulation frequency
	ampModulation = ampM;	// Set modulation amplitude
}

double T4fmValue() {
	double t = T4getTime(); // Get the current time
	return ampCarrier * sin(2 * PI * freqCarrier * t + ampModulation * sin(2 * PI * freqModulation * t)); // Voltage value
}

double T4fmValue(double t) {
	return ampCarrier * sin(2 * PI * freqCarrier * t + ampModulation * sin(2 * PI * freqModulation * t)); // Voltage value
}

/** Interrupt service routine that is executed at a compare match of GPT1.
 */
static void T4interrupt1() {
	GPT1_SR |= GPT_SR1;			// Reset the interrupt in the state register
	while (GPT1_SR & GPT_OC1);	// Wait for the register to be reset
	timer += (GPT1_OCR1 - timerRefreshed) + 1;	// Update global timer
	timerRefreshed = 0;							// Timer has been updated at the interrupt (GPT1 = 0)
	// If there is a function attached to the interrupt, execute it
	if(GPT1InUse) {
		(*(in1))();
	}
}

/** Interrupt service routine that is executed at a compare match of GPT2.
 */
static void T4interrupt2() {
	GPT2_SR |= GPT_SR1;			// Reset the interrupt in the state register
	while (GPT2_SR & GPT_OC1);	// Wait for the register to be reset
	// If there is a function attached to the interrupt, execute it
	if(GPT2InUse) {
		(*(in2))();
	}
}

void T4TimerInit() {
	CCM_CSCMR1 &= SCMR1_CLK_RT;						// Choose root clock (150 MHz)
	
	// Configure GPT1
	CCM_CCGR1 |= CGR1_GPT1;							// Activate clock for GPT1 module
	GPT1_CR = 0;									// Reset control register
	GPT1_PR = 0;									// Prescaling = 1:1
	GPT1_CR |= GPT_CR_PER;							// Choose peripheral clock auswählen for maximum speed (150 MHz)
	GPT1_CR |= GPT_CR_ENA;							// Activate timer counter GPT1
	GPT1_OCR1 = T4ccRate - 1;						// Set compare value to trigger the interrupt (1 Hz)
	GPT1_IR |= GPT_OC1;								// Activate the compare match 1
	attachInterruptVector(IRQ_GPT1, T4interrupt1);	// Set interrupt function
	NVIC_ENABLE_IRQ(IRQ_GPT1);						// Activate interrupt in the nested vector interrupt controller
	
	// Configure GPT2
	CCM_CCGR0 |= CGR1_GPT2;							// Activate clock for GPT1 module
	GPT2_CR = 0;									// Reset control register
	GPT2_PR = 0;									// Prescaling = 1:1
	GPT2_CR |= GPT_CR_PER;							// Choose peripheral clock auswählen for maximum speed (150 MHz)
	GPT2_CR |= GPT_CR_ENA;							// Activate timer counter GPT1
	GPT2_OCR1 = T4ccRate - 1;						// Set compare value to trigger the interrupt (1 Hz)
	GPT2_IR = GPT_OC1;								// Activate the compare match 1
	attachInterruptVector(IRQ_GPT2, T4interrupt2);	// Set interrupt function
	NVIC_ENABLE_IRQ(IRQ_GPT2);						// Activate interrupt in the nested vector interrupt controller
}

void T4interSetup(uint8_t timer, float interval) {
	uint32_t compare = interval * T4ccRate;
	switch(timer) {
		case GPT1:	GPT1InUse = true;			// GPT1 now has an active ISR
					GPT1_OCR1 = compare - 1;	// Set value for triggering the interrupt
					break;

		case GPT2:	GPT2InUse = true;			// GPT2 now has an active ISR
					GPT2_OCR1 = compare - 1;	// Set value for triggering the interrupt
					break;
	}
}

int32_t T4toSignMag(int32_t a) {
	if(a < 0) {
		a ^= (1 << 31) - 1;
		a += 1;
	}
	return a;
}

int32_t T4toExzess(int32_t a) {
	a += 1 << 31;
	return a;
}

int32_t T4to1Comp(int32_t a) {
	if(a < 0) {
		a -= 1;
	}
	return a;
}

// Simplified serial communication

void T4sBg(long baud) {
  if(baud > 4000000) {baud = 4000000;}	// Check for wrong values
  Serial.begin(baud);					// Begin serial communication
  // Ensure that the serial bus doesn't send garbage
  for(int i = 0; i < 100; i++) {
    Serial.read();
    delay(10);
    if(Serial.available() > 0) {
      i = 0;
    }
  }
}
void T4sBg() {T4sBg(9600);}

char* T4serialBuffer() {
	return serialBuffer;
}

void T4clearSerialBuffer() {
	serialBuffer[0] = '\0';	// Let string end with the first character
}

void T4checkSerialBuffer() {
	if(!newCommand) {return;}	// If there is no new command, nothing needs to be done
	//T4dw(9, HIGH);
	for(int i = 0; i < numSerialFuncs; i++) {
		bool b = serialFuncs[i](serialBuffer);	// Check command
		if(b) {									// Check wether command has been processed sucessfully
			T4dw(SucessPin, HIGH);				// Set pin to indicate that a command was proccessed successfully to HIGH
			T4dw(FailPin, LOW);					// Set pin to indicate that processing a command failed to LOW
			break;								// If the command has been processed successfully, no more checks are needed
		}
		else {
			T4dw(FailPin, HIGH);				// Set pin to indicate that processing a command failed to HIGH
		}
	}
	T4clearSerialBuffer();		// Clear buffer
	newCommand = false;			// Set flag that there is no new command
	T4dw(FailPin, LOW);			// Set pin to indicate that processing a command failed to LOW
	T4dw(SucessPin, LOW);		// Set pin to indicate that a command was proccessed successfully to LOW
	//T4dw(9, LOW);
}

void T4setSerialPulseTime(int t) {
	if(t < 0) {t = 0;}
	pulseTime = t;
}

void T4addSerialFunc(bool (*func)(String a)) {
	if(numSerialFuncs >= T4maxSerialFuncs) {return;}	// Check wether the array is already full
	serialFuncs[numSerialFuncs] = func;					// Add the function
	numSerialFuncs++;									// Increment the number of functions
}

/** This function is executed whenever theres is data available on the serial bus.
 */
void serialEvent() {
	if(checkingBuffer) {return;}	// If the content is currently being checked, it isn't overwritten
	// Read all abailable bytes and store them in the buffer (until the line ends)
	while(T4sa() > 0) {
		char val = Serial.read();					// Read character
		if(val == '\n') {							// End at the newline character
			serialBuffer[bufferPos] = '\0';			// Terminate the string with a NULL character
			bufferPos = 0;							// Return to the start of the buffer
			newCommand = true;						// Set flag for a new command to be checked
			break;
		}
		serialBuffer[bufferPos] = val;				// Write character to buffer
		bufferPos = (bufferPos + 1) % bufferLen;	// Go to the next position in the buffer
	}
}

void T4foo() {}
