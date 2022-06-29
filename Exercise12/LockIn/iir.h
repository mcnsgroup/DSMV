const int Niirmax = 200;
float ynhist[2][Niirmax];
float xnhist[2][Niirmax];

const int Nstep = 3;
int Niir = 2;

const float B = 1.931851652578;
float Omega = 0;//2 * cutoff / samplefreq;
float T = 2*tan(Omega * PI/2);
float b2 = (T*T)/(4+T*T+2*B*T);
float b1 = (2*T*T)/(4+T*T+2*B*T);
float b0 = (T*T)/(4+T*T+2*B*T);
float a2 = (-2*B*T+4+T*T)/(4+T*T+2*B*T);
float a1 = (2*T*T-8)/(4+T*T+2*B*T);
float a0 = 1;
const int Nb = Nstep;
float bn[Nb] = {
  b0, b1, b2
};
const int Na = Nstep;
float an[Na] = {
                a0, a1, a2
};

/** @brief Calculates the coefficients for an IIR filter
 *  
 *  @param props standardized properties array with the following order:
 *    props[0] holds the cutoff frequency
 *    props[5] holds the processing frequency
 */
void init_iir(float props[]) {
  for(int n = 0; n < Niirmax; n++){
    for(int i = 0; i < 2; i++){
      ynhist[i][n] = 0;
      xnhist[i][n] = 0;
    }
  }
  Omega = 2 * props[0] / props[5];
  T = 2*tan(Omega * PI/2);
  bn[2] = (T*T)/(4+T*T+2*B*T);
  bn[1] = (2*T*T)/(4+T*T+2*B*T);
  bn[0] = (T*T)/(4+T*T+2*B*T);
  an[2] = (-2*B*T+4+T*T)/(4+T*T+2*B*T);
  an[1] = (2*T*T-8)/(4+T*T+2*B*T);
}

/** @brief Applies an IIR filter to a signal
 *  
 *  This version calculates two signals at once, 
 *  in case of the lock-in, these are the regular and phase shifted signal
 *  
 *  @param xn analog input value
 *  @param props standardized properties array with the following order:
 *	  props[0] holds the cutoff frequency
 *    props[2] holds the filter order
 *    props[5] holds the processing frequency
 *  @return Resulting signal values
 */
float* proc_iir(float xn[], float props[]) {
  static float yn[2];
  yn[0] = 0.0;
  yn[1] = 0.0;
  // calculate first part of the sum
  for(int i=min(Niirmax, Nb)-1; i>0; i--) {
    // shift values by one
    xnhist[0][i] = xnhist[0][i-1];
    xnhist[1][i] = xnhist[1][i-1];
    // calculate response
    yn[0] += bn[i]*xnhist[0][i];
    yn[1] += bn[i]*xnhist[1][i];
  }
  // current sample
  xnhist[0][0] = xn[0];
  xnhist[1][0] = xn[1];
  yn[0] += bn[0]*xnhist[0][0];
  yn[1] += bn[0]*xnhist[1][0];
  // calculate second part of the sum
  for(int i=min(Niirmax, Na)-1; i>1; i--) {
    // shift values by one
    ynhist[0][i-1] = ynhist[0][i-2];
    ynhist[1][i-1] = ynhist[1][i-2];
    // calculate response
    yn[0] -= an[i]*ynhist[0][i-1];
    yn[1] -= an[i]*ynhist[1][i-1];
  }
  yn[0] -= an[1]*ynhist[0][0];
  yn[1] -= an[1]*ynhist[1][0];
  ynhist[0][0] = yn[0];
  ynhist[1][0] = yn[1];
  return yn;
}
