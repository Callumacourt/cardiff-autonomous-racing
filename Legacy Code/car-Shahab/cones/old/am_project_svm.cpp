#include "mex.h"
#include <math.h>
#include <vector>

// Project onto AM basis and apply linear transform, then score the result with SVM.

#define MAX_SD 3.2
#define SQUARE(x) ((x) * (x))

float const *X;
float const *B;
float const *avg;
float const *scale_a;
float const *scale_b;
float const *sd;
float *vectors;
float *alphas;
float bias;

int N;   // Number of data points
int dim; // Dimensionality of data
int Nb;  // Number of basis vectors
int Nv;  // Number of support vectors (and alphas)

inline float predict(float const *x, float const *vectors, float const *alphas, float const b, float const scale)
{
  float res = 0.0;
#pragma omp parallel for schedule(guided) reduction (+:res)
  for (int i = 0; i < Nv; ++i)
    {
      float const *v = vectors + i * Nb;
      float sum = 0.0;
#pragma omp simd reduction(+:sum)
      for (int j = 0; j < Nb; ++j)
        {
	  sum += SQUARE(x[j] - v[j]);
        }
      res += alphas[i] * exp(-sum * scale);
    }
  return res + b;
}

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

  if (6 != nrhs) {
    mexErrMsgTxt("Expected six arguments.\n");
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

  // Support vectors
  mxArray const* vectors_ = prhs[2];
  mwSize const* vecdims = mxGetDimensions(vectors_);
  Nv = vecdims[1];
  vectors = (float*)mxGetData(vectors_);

  // Alphas
  mxArray const* alphas_ = prhs[3];
  alphas = (float*)mxGetData(alphas_);

  // Bias
  mxArray const* bias_ = prhs[4];
  bias = *((float*)mxGetData(bias_));

  // Scale
  mxArray const* scale_ = prhs[5];
  double scale = *((float*)mxGetData(scale_));

  // Output
  plhs[0] = mxCreateNumericMatrix(1, N, mxSINGLE_CLASS, mxREAL);
  float *result = (float*)mxGetData(plhs[0]);

  std::vector<float> proj(Nb);
  for (float const *X_end = X + N * dim; X != X_end; X += dim) {
    float const *b = B;
    project(&proj[0], b, X);
    *result++ = predict(&proj[0], vectors, alphas, bias, scale);
  }
}
