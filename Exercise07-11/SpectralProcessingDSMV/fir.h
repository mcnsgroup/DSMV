#define MfilterMax 70                         /**< Maximum half filter order. */
const uint16_t NfilterMax = 2*MfilterMax + 1; /**< Maximum filter order plus 1. */
float filtercoeff[NfilterMax];                /**< Filtercoeffitients. */
//float dataBuffer[NfilterMax];
float dataBuffer[2*NfilterMax];               /**< Data buffer (double size for faster ring buffer acesss. */
//int32_t dataBufferInt[NfilterMax];
int32_t dataBufferInt[2*NfilterMax];          /**< Data buffer (raw values, double size for faster ring buffer acess). */
//int64_t filtercoeffInt[NfilterMax];
int32_t filtercoeffInt[NfilterMax];           /**< Filtercoefficients multiplied by 2^coeffPrec for integer arithmetc. */
uint16_t fir_bufPos = 0;                      /**< Current position in the data buffer. */

double phi = 0;     /**< Digital filter frequency. */
double phihigh = 0; /**< Digital filter frequency. */

#define rectWin     0       /**< Rectangle window. */
#define hammingWin  1       /**< Hamming window. */
#define integerArithmetic 0 /**< Integer arithmetic. */
#define floatArithmetic 1   /**< Float arithmetic. */
#define coeffPrec 9         /**< Precision (bits) of the FIR filter coefficients for integer arithmetic. */

/** @brief Multiplies a value by its factor from a window function.
 *  
 *  Coefficients are computed in both float and integer format. The integer coefficients are shifted by @coeffPrec bits.
 *  
 *  @param hi input value
 *  @param i index in the window function
 *  @param props standardized properties array with the following order:
 *    props[2] holds the filter order
 *    props[3] holds the filter window, currently supported are;
 *      rectWin Rectangle window
 *      hammingWin Hamming window
 *  @return resulting value
 */
float windowfunc(float hi, int i, float props[]) {
  float hw = 0;
  if(props[3] == hammingWin) {
    hw = hi * (0.54 - 0.46 * cos(2 * PI * i / (props[2] - 1)));       
  } else {
    hw = hi;
  }
  return hw;
}

/** @brief Initializes the filter coefficients h_k for the specified filter type.
 *  
 *  Coefficients are computed in both float and integer format. The integer coefficients are shifted by @coeffPrec bits.
 *  
 *  @param type filter type, currently supported are:
 *    movingAvg Moving average
 *    FIRlow FIR low pass filter
 *    FIRhigh FIR high pass filter
 *    bandpass FIR bandpass filter
 *    bandstop FIR bandstop filter
 *  @param props standardized properties array with the following order:    
 *    props[0] holds the cutoff frequency (if applicable)
 *    props[1] holds the second cutoff frequency (if applicable)
 *    props[2] holds the filter order
 *    props[3] holds the filter window, currently supported are;
 *      rectWin Rectangle window
 *      hammingWin Hamming window
 *    props[5] holds the processing frequency
 */
void init_fir(uint8_t type, float props[]) {
  uint16_t Nfilter = props[2];
  uint16_t Mfilter = (Nfilter-1)/2;
  switch(type) {
    // Moving average
    case movingAvg: 
      for(int i = 0; i < Nfilter; i++) {
         filtercoeff[i] = 1.0 / Nfilter;
         filtercoeffInt[i] = (1 << coeffPrec) / Nfilter;
      }
    break;

    // Low pass filter
    case FIRlow:
      phi = 2 * PI * props[0] / props[5];
      for(int i = 0; i < Nfilter; i++) {
        double hk = sin(phi * (i - Mfilter)) / (PI * (i - Mfilter));
        filtercoeff[i] = windowfunc(hk, i, props);
        filtercoeffInt[i] = windowfunc((1 << coeffPrec) * hk, i, props);
      }
      filtercoeff[Mfilter] = phi / PI;
      filtercoeffInt[Mfilter] = (1 << coeffPrec) * phi / PI;
      break;

    // High pass filter
    case FIRhigh:
      phi = 2 * PI * props[0] / props[5];
      for(int i = 0; i < Nfilter; i++) {
        double hk = -sin(phi * (i - Mfilter)) / (PI * (i - Mfilter)); 
        filtercoeff[i] = windowfunc(hk, i, props);
        filtercoeffInt[i] = windowfunc((1 << coeffPrec) * hk, i, props);
      }
      filtercoeff[Mfilter] = (1-phi / PI);
      filtercoeffInt[Mfilter] = (1 << coeffPrec) * (1-phi / PI);
      break;

    // Bandpass filter
    case bandpass:
      phi = 2 * PI * props[0] / props[5];
      phihigh = 2 * PI * props[1] / props[5];
      for(int i = 0; i < Nfilter; i++) {
        double hk = ((sin(phihigh * (i - Mfilter)) - sin(phi * (i - Mfilter))) / (PI * (i - Mfilter)));
        filtercoeff[i] = windowfunc(hk, i, props);
        filtercoeffInt[i] = windowfunc((1 << coeffPrec) * hk, i, props);
      }
      filtercoeffInt[Mfilter] = (1 << coeffPrec) * ((phihigh-phi) / PI);
      filtercoeff[Mfilter] = ((phihigh-phi) / PI);
      break;

    // Bandstop filter
    case bandstop:
      phi = 2 * PI * props[0] / props[5];
      phihigh = 2 * PI * props[1] / props[5];
      for(int i = 0; i < Nfilter; i++) {
        double hk = -((sin(phihigh * (i - Mfilter)) - sin(phi * (i - Mfilter))) / (PI * (i - Mfilter)));
        filtercoeff[i] = windowfunc(hk, i, props);
        filtercoeffInt[i] = windowfunc((1 << coeffPrec) * hk, i, props);
      }
      filtercoeff[Mfilter] = (1-(phihigh-phi) / PI);
      filtercoeffInt[Mfilter] = (1 << coeffPrec) * (1-(phihigh-phi) / PI);
      break;
  }
}

/** @brief Implements a FIR filter
 *  
 *  There are mutliple optimizations to be considered for this filter.
 *  When acessing and processing the input values and filter coefficients, 
 *  one can choose between integer and float arithmetic.
 *  Moreover, the data buffer can be acessed as a ring buffer using modulo,
 *  using an if-comparator or using a double-sized buffer.
 *  For testing which method is the fastest, the following settings were used with a bandpass filter:
 *    f_p = 80000Hz
 *    N = 1000
 *    f_low = 2000
 *    f_high = 4000
 *    Nfilter = 140
 *  The results were as follows:
 *  Integer arithmetic:
 *    Modulo        3.27µs
 *    If            1.96µs
 *    double buffer (1.02 + 0.8)µs / 2, for some reason this is sometimes faster and sometimes slower
 *  Float arithmetic:
 *    Modulo        3.95µs
 *    If            1.71µs
 *    double buffer 1.7µs
 *  
 *  @param xn analog input value (V)
 *  @param xnRaw raw analog input value
 *  @param props standardized properties array with the following order:		
 *      props[2] holds the filter order
 *      props[4] holds the arithmetic, currently supported are:
 *         integerArihtmetic  integer arithmetic
 *         floatArithmetic  float arithmetic
 *  @param arithmetic arithmetic to be used for computation of the result, currently supported are:
 *    integerArithmetic integer arithmetic
 *    floatArithmetic float arithmetic
 *  @return Resulting signal value
 */
float proc_fir(float xn, int32_t xnRaw, float props[]) {
  uint16_t Nfilter = props[2];
  // Write value to data buffer
  dataBuffer[fir_bufPos] = xn;
  dataBuffer[fir_bufPos + Nfilter] = xn;
  dataBufferInt[fir_bufPos] = xnRaw >> (coeffPrec - 7);
  dataBufferInt[fir_bufPos + Nfilter] = xnRaw >> (coeffPrec - 7);
  // Next buffer position
  fir_bufPos = (fir_bufPos + 1) % Nfilter;
  float filtered = 0;
  //int64_t filteredInt = 0;
  int32_t filteredInt = 0;
  switch((int) props[4]) {
    case integerArithmetic: // Measure timing
    						            //T4toggle(LED_3);
                            for(int i = 0; i < Nfilter; i++) {
                              // Computation using if based modulo
                              /*if(fir_bufPos + i >= Nfilter) {
                                filteredInt += dataBufferInt[fir_bufPos + i - Nfilter] * filtercoeffInt[i];
                              }
                              else {
                                filteredInt += dataBufferInt[(fir_bufPos + i)] * filtercoeffInt[i];
                              }*/
                              // Computation using double buffer
                              filteredInt += dataBufferInt[fir_bufPos + i] * filtercoeffInt[i];
                            }
                            //T4toggle(LED_3);
                            // Shift by factor of the coefficient array
                            filtered = filteredInt >> 7;
                            // Convert into a voltage
                            filtered = RES_LTC2500 * filtered; 
                            // Offset/gain correction
                            filtered = filtered * gainLTC2500 + offsetLTC2500;
                            break;
    case floatArithmetic:   // Measure timing
    						            //T4toggle(LED_3);
                            for(int i = 0; i < Nfilter; i++) {
                              // Computation using if based modulo
                              /*if(fir_bufPos + i >= Nfilter) {
                                filtered += dataBuffer[fir_bufPos + i - Nfilter] * filtercoeff[i];
                              }
                              else {
                                filtered += dataBuffer[(fir_bufPos + i)] * filtercoeff[i];
                              }*/
                              // Computation using double buffer
                              filtered += dataBuffer[fir_bufPos + i] * filtercoeff[i];
                            }
                            //T4toggle(LED_3);
  }
  return filtered;
}
