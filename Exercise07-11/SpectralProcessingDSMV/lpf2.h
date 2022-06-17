/* history values for lpf2 */
float yl2n_1 = 0.0;
float yl2n_2 = 0.0;

/** @brief Implements a low-pass filter of 2nd order
 *  
 *  @param xn analog input value
 *  @param props standardized properties array with the following order:		
 *		props[0] holds the cutoff frequency
 *		props[5] holds the processing frequency
 *  @return Resulting signal value
 */
float proc_lpf2(float xn, float props[]) {
  float fswc = props[5]/(2*PI*props[0]);
  float fac  = 1 + 2*fswc + fswc*fswc;
  float fac2 = 2*fswc + 2*fswc*fswc;
  float fac3 = fswc*fswc;
  float out = 1.0/fac*(fac2*yl2n_1 - fac3*yl2n_2 + xn);
  yl2n_2 = yl2n_1;
  yl2n_1 = out;
  return out;
}
