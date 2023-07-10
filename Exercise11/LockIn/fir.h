#define MfilterMax 100                        /**< Maximum half filter order. */
const uint16_t NfilterMax = 2*MfilterMax + 1; /**< Maximum filter order plus 1. */
float filtercoeff[NfilterMax];                /**< Filtercoeffitients. */
float dataBuffer[2][2*NfilterMax];            /**< Data buffer (double size for faster ring buffer acesss. */
int32_t dataBufferInt[2][2*NfilterMax];       /**< Data buffer (raw values, double size for faster ring buffer acess). */
int32_t filtercoeffInt[NfilterMax];           /**< Filtercoefficients multiplied by 2^coeffPrec for integer arithmetc. */
uint16_t fir_bufPos = 0;                      /**< Current position in the data buffer. */

double phi = 0;     /**< Digital filter frequency. */
double phihigh = 0; /**< Digital filter frequency. */

#define rectWin     0         /**< Rectangle window. */
#define hammingWin  1         /**< Hamming window. */
#define integerDoubleBuffer 0 /**< Integer arithmetic with a double sized buffer. */
#define integerIfModulo 1     /**< Integer arithmetic with an if based modulo. */
#define integerModulo 2       /**< Integer arithmetic with a regular modulo. */
#define floatDoubleBuffer 3   /**< Float arithmetic with a double sized buffer. */
#define floatIfModulo 4       /**< Float arithmetic with an if based modulo. */
#define floatModulo 5         /**< Float arithmetic with a regular modulo. */
#define coeffPrec 9           /**< Precision (bits) of the FIR filter coefficients for integer arithmetic. */

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
 *         floatDoubleBuffer  float arithmetic
 *  @param arithmetic arithmetic to be used for computation of the result, currently supported are:
 *    integerDoubleBuffer integer arithmetic
 *    floatDoubleBuffer float arithmetic
 *  @return Resulting signal value
 */
float* proc_fir(float xn[], int32_t xnRaw[], float props[]) {
  uint16_t Nfilter = props[2];
  // Write value to data buffer
  dataBuffer[0][fir_bufPos] = xn[0];
  dataBuffer[1][fir_bufPos] = xn[1];
  dataBuffer[0][fir_bufPos + Nfilter] = xn[0];
  dataBuffer[1][fir_bufPos + Nfilter] = xn[1];
  dataBufferInt[0][fir_bufPos] = xnRaw[0] >> (coeffPrec - 7);
  dataBufferInt[1][fir_bufPos] = xnRaw[1] >> (coeffPrec - 7);
  dataBufferInt[0][fir_bufPos + Nfilter] = xnRaw[0] >> (coeffPrec - 7);
  dataBufferInt[1][fir_bufPos + Nfilter] = xnRaw[1] >> (coeffPrec - 7);
  // Next buffer position
  fir_bufPos = (fir_bufPos + 1) % Nfilter;
  
  static float filtered[2];
  filtered[0] = 0;
  filtered[1] = 0;
  static int32_t filteredInt[2];
  filteredInt[0] = 0;
  filteredInt[1] = 0;
  // Measure timing - has been moved to main program
  //T4toggle(LED_3);
  // Note: The integer arithmetic yields no useful result.
  switch((int) props[4]) {
    case integerDoubleBuffer: for(int i = 0; i < Nfilter; i++) {
                                filteredInt[0] += dataBufferInt[0][fir_bufPos + i] * filtercoeffInt[i];
                                filteredInt[1] += dataBufferInt[1][fir_bufPos + i] * filtercoeffInt[i];
                              }
                              // Shift by factor of the coefficient array
                              filtered[0] = filteredInt[0] >> 7;
                              filtered[1] = filteredInt[1] >> 7;
                              break;
    case integerIfModulo:     for(int i = 0; i < Nfilter; i++) {
                                if(fir_bufPos + i >= Nfilter) {
                                  filteredInt[0] += dataBufferInt[0][fir_bufPos + i - Nfilter] * filtercoeffInt[i];
                                  filteredInt[1] += dataBufferInt[1][fir_bufPos + i - Nfilter] * filtercoeffInt[i];
                                }
                                else {
                                  filteredInt[0] += dataBufferInt[0][(fir_bufPos + i)] * filtercoeffInt[i];
                                  filteredInt[1] += dataBufferInt[1][(fir_bufPos + i)] * filtercoeffInt[i];
                                }
                              }
                              // Shift by factor of the coefficient array
                              filtered[0] = filteredInt[0] >> 7;
                              filtered[1] = filteredInt[1] >> 7;
                              break;
    case integerModulo:       for(int i = 0; i < Nfilter; i++) {
                                filteredInt[0] += dataBufferInt[0][(fir_bufPos + i) % Nfilter] * filtercoeffInt[i];
                                filteredInt[1] += dataBufferInt[1][(fir_bufPos + i) % Nfilter] * filtercoeffInt[i];
                              }
                              // Shift by factor of the coefficient array
                              filtered[0] = filteredInt[0] >> 7;
                              filtered[1] = filteredInt[1] >> 7;
                              break;
    case floatDoubleBuffer:   for(int i = 0; i < Nfilter; i++) {
                                filtered[0] += dataBuffer[0][fir_bufPos + i] * filtercoeff[i];
                                filtered[1] += dataBuffer[1][fir_bufPos + i] * filtercoeff[i];
                              }
                              break;
    case floatIfModulo:       for(int i = 0; i < Nfilter; i++) {
                                if(fir_bufPos + i >= Nfilter) {
                                  filtered[0] += dataBuffer[0][fir_bufPos + i - Nfilter] * filtercoeff[i];
                                  filtered[1] += dataBuffer[1][fir_bufPos + i - Nfilter] * filtercoeff[i];
                                }
                                else {
                                  filtered[0] += dataBuffer[0][(fir_bufPos + i)] * filtercoeff[i];
                                  filtered[1] += dataBuffer[1][(fir_bufPos + i)] * filtercoeff[i];
                                }
                              }
                              break;
    case floatModulo:         for(int i = 0; i < Nfilter; i++) {
                                filtered[0] += dataBuffer[0][(fir_bufPos + i) % Nfilter] * filtercoeff[i];
                                filtered[1] += dataBuffer[1][(fir_bufPos + i) % Nfilter] * filtercoeff[i];
                              }
                              break;
  }
  //T4toggle(LED_3);
  return filtered;
}
