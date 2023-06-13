/* historic value */
float yown_n1 = 0.0;

/** @brief Implements a low-pass filter of 1st order
 *  
 *  IO-equation: y_n = 1/(f_p/(2*PI*f_c)+1)*(xn + f_p/(2*PI*f_c)*y_{n-1})
 *  
 *  @param xn analog input value
 *  @param props standardized properties array with the following order:		
 *		props[5] holds the processing frequency
 *  @return Resulting signal value
 */
float proc_ownDef(float xn, float props[]) {
  float fc = 500; 
  float fac = props[5]/(2.0*PI*fc);
  float out = xn;  //TODO
  yown_n1 = out;
  return out;
}
