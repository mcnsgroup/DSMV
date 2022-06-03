/** @brief Amplifies or attenuates a signal by given factor 
 *  
 *  IO-equation: y_n = factor * x_n
 *  
 *  @param value analog input value
 *  @param props standardized properties array with the following order:
 		prop[0] holds the amplification (factor>1.0) or attenuation (factor<1.0) factor
 *  @return Resulting signal value
 */
float proc_scale(float value, float props[]) {
  return value*props[0];
}
