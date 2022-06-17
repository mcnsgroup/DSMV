/** @brief Amplifies or attenuates a signal by given factor 
 *  
 *  IO-equation: y_n = factor * x_n
 *  
 *  @param value analog input value
 *  @param props standardized properties array with the following order:
 *		prop[0] holds the amplification (factor>1.0) or attenuation (factor<1.0) factor
 *  @return Resulting signal value
 */
float proc_scale(float value, float props[]) {
  return value*props[0];
}

/** @brief Amplifies or attenuates a signal by given factor using integer arithmetic
 *  
 *  IO-equation: y_n = factor * x_n
 *  
 *  @param value raw analog input value
 *  @param props standardized properties array with the following order:
     prop[0] holds the amplification multiplied by 2^32 (factor>1.0*2^32) or attenuation (factor<1.0*2^32) factor
 *  @return Resulting signal value
 */
float proc_scale(int32_t value, int64_t props[]) {
  return (value * props[0]) >> 32;
}
