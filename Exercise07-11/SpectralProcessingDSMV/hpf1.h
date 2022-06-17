/* history values for hpf1 */
float xhn_1 = 0.0;
float yhn_1 = 0.0;

/** @brief Implements a high-pass filter of 1st order
 *  
 *  IO-equation: y_n = 1/(f_p/(2*PI*f_c)+1)*(xn + y_{n-1} - x_{n-1})
 *  
 *  @param xn analog input value
 *  @param props standardized properties array with the following order:		
 *		props[0] holds the cutoff frequency
 *		props[5] holds the processing frequency
 *  @return Resulting signal value
 */
float proc_hpf1(float xn, float props[]) {
  float fac = (2.0*PI*props[0])/props[5];
  float out = 1.0/(fac+1.0)*(xn + yhn_1-xhn_1);
  yhn_1 = out;
  xhn_1 = xn;
  return out;
  
}
