#include "mex.h"
#include <math.h>

// Project onto AM basis and apply linear transform to the result

float const *X;
float const *B;
// float const *avg;
// float const *scale_a;
// float const *scale_b;

int N;   // Number of data points
int dim; // Dimensionality of data
int Nb;  // Number of basis vectors

inline void project(float *proj, float const* B, float const *X)
{
#pragma omp parallel for schedule(guided)
  for (int j = 0; j < Nb; ++j)
    {
      float const *b = B + j * dim;
      float sum = 0.0;
#pragma omp simd reduction(+:sum)
      for (int k = 0; k < dim; ++k)
        {
          sum += X[k] * b[k];
        }
      proj[j] = sum;
    }
}

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {

  if (2 != nrhs) {
    mexErrMsgTxt("Expected two arguments.\n");
    return;
  }

  // Data
  mxArray const* X_ = prhs[0];
  mwSize const* Xdims = mxGetDimensions(prhs[0]);
  dim = Xdims[0]; N = Xdims[1];
  X = (float const*)mxGetData(X_);

  // Basis vectors
  mxArray const* B_ = prhs[1];
  mwSize const* Bdims = mxGetDimensions(prhs[1]);
  Nb = Bdims[1];
  B = (float const*)mxGetData(B_);

  // // Average
  // avg = (float const*)mxGetData(prhs[2]);

  // // Scale A
  // scale_a = (float const*)mxGetData(prhs[3]);

  // // Scale B
  // scale_b = (float const*)mxGetData(prhs[4]);

  // Output
  plhs[0] = mxCreateNumericMatrix(Nb, N, mxSINGLE_CLASS, mxREAL);
  float *result = (float*)mxGetData(plhs[0]);

  for (int i = 0; i < N; ++i) {
    project(result + i * Nb, B, X);
  }
}
