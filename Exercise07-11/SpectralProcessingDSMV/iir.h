const int Niirmax = 200;
float ynhist[Niirmax];
float xnhist[Niirmax];

#include "fdacoeffs.h"

/** @brief Applies an IIR filter to a signal
 *  
 *  @param xn analog input value
 *  @param props standardized properties array with the following order:
 *		The properties for this filter are ignored as they are defined externally or directly in this file.
 *  @return Resulting signal value
 */
float proc_iir(float xn, float props[]) {
  float yn = 0.0;
  // calculate first part of the sum
  for(int i=min(Niirmax, Nb)-1; i>0; i--) {
    // calculate response
    yn += bn[i]*xnhist[i];
    // shift values by one
    xnhist[i] = xnhist[i-1];
  }
  // current sample
  yn += bn[0]*xnhist[0];
  xnhist[0] = xn;
  // calculate second part of the sum
  for(int i=min(Niirmax, Na)-1; i>1; i--) {
    // shift values by one
    ynhist[i-1] = ynhist[i-2];
    // calculate response
    yn -= an[i]*ynhist[i-1];
  }
  yn -= an[1]*ynhist[0];
  ynhist[0] = yn;

  return yn;
}
