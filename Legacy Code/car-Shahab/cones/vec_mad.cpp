#include "mex.h"
#include <math.h>
// #include <vector>
// #include <algorithm>

// Compute mean absolute error columnwise.

float const *X;
float const *vec;
float const *mask;
int N;   // Number of data points
int dim; // Dimensionality of data


void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {

  if (3 != nrhs) {
    mexErrMsgTxt("Expected three arguments.\n");
    return;
  }

  // Data
  mxArray const* X_ = prhs[0];
  mwSize const* Xdims = mxGetDimensions(prhs[0]);
  dim = Xdims[0]; N = Xdims[1];
  X = (float const*)mxGetData(X_);

  // Vector
  mxArray const* vec_ = prhs[1];
  vec = (float const*)mxGetData(vec_);

  // Mask
  mxArray const* mask_ = prhs[2];
  mask = (float const*)mxGetData(mask_);

  // Output
  plhs[0] = mxCreateNumericMatrix(1, 1, mxSINGLE_CLASS, mxREAL);
  float *result = (float*)mxGetData(plhs[0]);

  // std::vector<float> diff(dim);

  // int Nbest = (int)(0.75 * (double)dim);
  //   double sum = 0.0;
  //   for (int i = 0; i < N; ++i) {
  //     float const *x = X + dim * i;
  //     for (int j = 0; j < dim; ++j) {
  //       diff[j] = fabs(vec[j] - x[j]);
  //     }
  //     std::sort(diff.begin(), diff.end());
  //     for (int j = 0; j < Nbest; ++j) {
  // 	sum += diff[j];
  //     }
	
  //   }


    double sum = 0.0;
#pragma omp parallel for reduction (+:sum)
  for (int i = 0; i < N; ++i) {
    float const *x = X + dim * i;
    for (int j = 0; j < dim; ++j) {
      sum += fabs(vec[j] - x[j]) * mask[j];
    }      
  }

  *result = sum / (float)(N * dim);
}
