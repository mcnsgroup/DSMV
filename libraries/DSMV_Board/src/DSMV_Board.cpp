#include "DSMV_Board.h"

/**	These definitions provide the values for external variables used in the .cpp files of various libraries 
 *	associated with the DSMV Board (i. e. AD4020.cpp).
 *	Due to the nature of external variables, they can't be defined in the header file but must be in the .cpp file.
 */

uint32_t ccRate = T4ccRate;				/**< Frequency of the timer counter (Hz) */
uint8_t T4mosi = MOSI_DAC;				/**< MOSI Pin for sending data via the SPI bus (adjustable). */
uint8_t T4miso = MISO_DAC;				/**< MOSI Pin für receiving data via the SPI bus (adjustable). */
uint8_t T4sclk = SCLK_DAC;				/**< SCLK Pin für sending and receiving data via the SPI bus (adjustable). */
uint8_t TimerPin = LED_1;				/**< Pin to measure exact timings (for debugging purposes). */
uint8_t DebugPin = LED_2;				/**< Pin to indicate debug state. */
uint8_t SucessPin = LED_3;				/**< Pin to indicate that a command was proccessed successfully. */
uint8_t FailPin = LED_2;				/**< Pin to indicate that processing a command failed. */
uint8_t CNV_AD4020 = AD4020_CNV;		/**< CNV pin of the AD4020 for its library. */
uint8_t SCLK_AD4020 = SCLK_ADC;			/**< SCLK pin of the AD4020 for its library. */
uint8_t MOSI_AD4020 = MOSI_ADC;			/**< MOSI pin of the AD4020 for its library. */
uint8_t MISO_AD4020 = MISO_ADC;			/**< MISO pin of the AD4020 for its library. */
uint8_t MCLK_LTC2500 = LTC2500_MCLK;	/**< MCLK pin of the LTC2500 for its library. */
uint8_t RDLA_LTC2500 = LTC2500_RDLA;	/**< RDLA pin of the LTC2500 for its library. */
uint8_t RDLB_LTC2500 = LTC2500_RDLB;	/**< RDLB pin of the LTC2500 for its library. */
uint8_t PRE_LTC2500 = LTC2500_PRE;		/**< PRE pin of the LTC2500 for its library. */
uint8_t DRL_LTC2500 = LTC2500_DRL;		/**< DRL pin of the LTC2500 for its library. */
uint8_t BUSY_LTC2500 = LTC2500_BUSY;	/**< BUSY pin of the LTC2500 for its library. */
uint8_t SCLK_LTC2500 = SCLK_ADC;		/**< SCLK pin of the LTC2500 for its library. */
uint8_t MOSI_LTC2500 = MOSI_ADC;		/**< MOSI pin of the LTC2500 for its library. */
uint8_t MISO_LTC2500 = MISO_ADC;		/**< MISO pin of the LTC2500 for its library. */
uint8_t SYNC_AD5791 = AD5791_SYNC;		/**< SYNC pin of the AD5791 for its library. */
uint8_t RESET_AD5791 = AD5791_RESET;	/**< RESET pin of the AD5791 for its library. */
uint8_t CLR_AD5791 = AD5791_CLR;		/**< CLR pin of the AD5791 for its library. */
uint8_t LDAC_AD5791 = AD5791_LDAC;		/**< LDAC pin of the AD5791 for its library. */
uint8_t SCLK_AD5791 = SCLK_DAC;			/**< SCLK pin of the AD5791 for its library. */
uint8_t MOSI_AD5791 = MOSI_DAC;			/**< MOSI pin of the AD5791 for its library. */

void setOutputPins() {
  const int num_outputs = 18;					// Number of output pin
  const int outputs[] = {LED_1, LED_2, LED_3,	// LEDs
                         AD4020_CNV,			// Convert pin of the AD4020
                         LTC2500_RDLB, LTC2500_RDLA, LTC2500_SYNC, LTC2500_MCLK, LTC2500_PRE,	// Control pins of the LTC2500
                         MOSI_ADC, SCLK_ADC,	// SPI bus for the ADCs
                         DAC_TEENSY,			// Output pin for the internen DAC
                         AD5791_SYNC, AD5791_RESET, AD5791_CLR, AD5791_LDAC,	// Control pins of the AD5791
                         MOSI_DAC, SCLK_DAC};	// SPI bus for the DAC
  T4pinSetup(outputs, num_outputs);				// Configure output pins
}

bool readSchmitt() {
  return T4dr(SCHMITT_TRIGGER);
}
