/* history value for lpf1 */
float yln_1 = 0.0;

/** @brief Implements a low-pass filter of 1st order
 *  
 *  IO-equation: y_n = 1/(f_p/(2*PI*f_c)+1)*(xn + f_p/(2*PI*f_c)*y_{n-1})
 *  
 *  @param xn analog input value
 *  @param props standardized properties array with the following order:		
 *		props[0] holds the cutoff frequency
 *		props[5] holds the processing frequency
 *  @return Resulting signal value
 */
float proc_lpf1(float xn, float props[]) {
  float fac = props[5]/(2.0*PI*props[0]);
  float out = 1.0/(fac+1.0)*(xn + fac*yln_1);
  yln_1 = out;
  return out;
}
