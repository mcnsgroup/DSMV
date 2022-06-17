/* Ring buffer for moving average filter */
#define Nmax 256
float dbuffer[Nmax];
int idbuffer = 0;

/** @brief Moving averaging filter
 *  
 *  IO-equation: y_n = sum_{k=n-N}^n x_k
 *  
 *  @param value analog input value
 *  @param props standardized properties array with the following order:
 *		props[0] holds the number of values to average over (N)
 *  @return Resulting signal value
 */
float proc_avg(float value, float props[]) {
  // store current value in buffer
  dbuffer[idbuffer] = value;

  // average the last <samples> values
  float avg = 0;
  for(int i=0; i<props[0]; i++) {
    if(idbuffer-i>=0) {
      avg += dbuffer[idbuffer-i];
    } else {
      avg += dbuffer[Nmax+(idbuffer-i)];
    }
  }
  avg/=props[0];
  
  // advance pointer
  idbuffer++;
  if(idbuffer>=Nmax) {
    idbuffer = 0;
  }
  
  return avg;
}
