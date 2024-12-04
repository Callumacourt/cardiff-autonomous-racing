#include "mex.h"
#include <math.h>
#include <vector>


float *X;
float *vectors;
float *alphas;
float bias;

int N;   // Number of data points
int dim; // Dimensionality of data (and support vectors)
int Nv;  // Number of support vectors (and alphas)

#define SQUARE(x) ((x) * (x))

inline float vnorm2(float const *a, float const *b) {
  float sum = 0.0;
  for (float const *a_end = a + dim; a != a_end; ++a, ++b) {
    sum += SQUARE(*a - *b);
  }
  return sum;
}

inline float predict(float const *x, float const *v, float const *a, float const b)
{
  float sum = 0.0;
#pragma omp simd reduction(+:sum)
  for (int i = 0; i < Nv; ++i) {
    sum += a[i] * exp(-vnorm2(x, v + i * dim));
  }
  return sum + b;
}

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {

  // if (4 != nrhs) {
  //   mexErrMsgTxt("Expected four arguments.\n");
  //   return;
  // }

  // Data
  mxArray const* X_ = prhs[0];
  mwSize const* Xdims = mxGetDimensions(prhs[0]);
  dim = Xdims[0]; N = Xdims[1];
  X = (float*)mxGetData(X_);

  // Support vectors
  mxArray const* vectors_ = prhs[1];
  mwSize const* vecdims = mxGetDimensions(prhs[1]);
  Nv = vecdims[1];
  vectors = (float*)mxGetData(vectors_);

  // Alphas
  mxArray const* alphas_ = prhs[2];
  alphas = (float*)mxGetData(alphas_);

  // Bias
  mxArray const* bias_ = prhs[3];
  bias = *((float*)mxGetData(bias_));

  // Output
  plhs[0] = mxCreateNumericMatrix(1, N, mxSINGLE_CLASS, mxREAL);
  float *result = (float *)mxGetData(plhs[0]);


  if (N > 1) {
#pragma omp parallel for schedule(static)
    for (int i = 0; i < N; ++i) {
      result[i] = predict(X + i * dim, vectors, alphas, bias);
    }
  }
  else {
    float res = 0.0;
#pragma omp parallel for schedule(guided) reduction (+:res)
    for (int j = 0; j < Nv; ++j) {
      float const *v = vectors + j * dim;
      float sum = 0.0;
      for (int k = 0; k < dim; ++k) {
        sum += SQUARE(X[k] - v[k]);
      }
      res += alphas[j] * exp(-sum);
    }
    *result = res + bias;
  }
}
