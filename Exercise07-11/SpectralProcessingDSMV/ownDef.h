/* variables for historic values y_{n-1} and y_{n-2} */
float yown_n1 = 0.0;
float yown_n2 = 0.0;
/* variables for historic values x_{n-1} and x_{n-2} */
float xown_n1 = 0.0;
float xown_n2 = 0.0;

/** @brief Offers the implementation of a filter
 *  
 *  @param xn analog input value (in 1V)
 *  @param props standardized properties array with the following order:		
 *		props[5] holds the processing frequency (in Hz)
 *  @return Resulting signal value (in 1V)
 */
float proc_ownDef(float xn, float props[]) {
  // corner frequency
  float fc = 500; 
  // factor alpha
  float alpha = props[5]/(2.0*PI*fc);

  // calculate y_n
  float yn = xn;  /** TODO **/

  // store historic values y_{n-1} and x_{n-1}
  yown_n1 = yn;
  xown_n1 = xn;

  // return y_n
  return yn;
}
