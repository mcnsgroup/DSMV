/* history values for lpf3 */
float yl3n_1 = 0.0;
float yl3n_2 = 0.0;
float yl3n_3 = 0.0;

/** @brief Implements a low-pass filter of 3rd order
 *  
 *  @param xn analog input value
 *  @param props standardized properties array with the following order:		
 *		prop[0] holds the cutoff frequency
 *		prop[3] holds the processing frequency
 *  @return Resulting signal value
 */
float proc_lpf3(float xn, float props[]) {
  float fswc = props[3]/(2*PI*props[0]);
  float fac  = 1 + 3*fswc + 3*fswc*fswc + fswc*fswc*fswc;
  float fac1 = 3*fswc + 6*fswc*fswc + 3*fswc*fswc*fswc;
  float fac2 = 3*fswc*fswc + 3*fswc*fswc*fswc;
  float fac3 = fswc*fswc*fswc;
  float out = 1.0/fac*(fac1*yl3n_1 - fac2*yl3n_2 + fac3*yl3n_3 + xn);
  yl3n_3 = yl3n_2;
  yl3n_2 = yl3n_1;
  yl3n_1 = out;
  return out;
}
