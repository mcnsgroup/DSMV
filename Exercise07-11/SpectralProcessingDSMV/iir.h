const int Niirmax = 200;
float ynhist[Niirmax];
float xnhist[Niirmax];

#include "fdacoefs20.h"

#ifndef real32_T
/****** low pass filter
float alpha = 25000/(2*PI*2000);
// factors xn
float an[] = {1/(alpha+1)};
// factors yn
float bn[] = {alpha/(alpha+1)};

/****** Butterworth low pass filter 
// factors xn
float an[] = {0.028635, 0.085906, 0.085906,  0.028635};
// factors yn
float bn[] = {-1.5189, 0.96, -0.2120};

/****** Chebyshevlow pass filter
// factors b_n (for x_n)
float bn[] = {0.0061888, 0.018566, 0.018566, 0.006188};
// factors a_n (for y_n). always use an[0]=1 
float an[] = {1, -2.342136, 2.0015668, -0.6099202};

int Na = sizeof(an)/sizeof(an[0]);
int Nb = sizeof(bn)/sizeof(bn[0]);
*/
#endif

/** @brief Applies an IIR filter to a signal
 *  
 *  @param xn analog input value
 *  @param props standardized properties array with the following order:
 *		The properties for this filter are ignored as they are defined externally or directly in this file.
 *  @return Resulting signal value
 */
float proc_iir(float xn, float props[]) {
  float yn = 0.0;
  for(int i=min(Niirmax, Nb)-1; i>0; i--) {
    // calculate response
    yn += bn[i]*xnhist[i];
    // shift values by one
    xnhist[i] = xnhist[i-1];
  }
  // current sample
  xnhist[0] = xn;
  yn += bn[0]*xn;

  for(int i=min(Niirmax, Na)-1; i>1; i--) {
    // calculate response
    yn -= an[i]*ynhist[i-1];
    // shift values by one
    ynhist[i-1] = ynhist[i-2];
    
  }
  yn -= an[1]*ynhist[0];
  ynhist[0] = yn;

  return yn;
}
