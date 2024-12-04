#include <Eigen/Dense>
using namespace Eigen;
#include "mex.h"
#include <math.h>


// Project onto AM basis and apply linear transform to the result

float *X;
float *B;
float *avg;
float *scale_a;
float *scale_b;

int N;   // Number of data points
int dim; // Dimensionality of data
int Nb;  // Number of basis vectors


void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {

  if (5 != nrhs) {
    mexErrMsgTxt("Expected five arguments.\n");
    return;
  }

  // Data
  mxArray const* X_ = prhs[0];
  mwSize const* Xdims = mxGetDimensions(prhs[0]);
  dim = Xdims[0]; N = Xdims[1];
  X = (float *)mxGetData(X_);

  // Basis vectors
  mxArray const* B_ = prhs[1];
  mwSize const* Bdims = mxGetDimensions(prhs[1]);
  Nb = Bdims[1];
  B = (float *)mxGetData(B_);

  // Average
  avg = (float *)mxGetData(prhs[2]);

  // Scale A
  scale_a = (float *)mxGetData(prhs[3]);

  // Scale A
  scale_b = (float *)mxGetData(prhs[4]);

  // Output
  plhs[0] = mxCreateNumericMatrix(Nb, N, mxSINGLE_CLASS, mxREAL);
  float *result = (float*)mxGetData(plhs[0]);


  Map<MatrixXf> _X(X, dim, N);
  Map<MatrixXf> _B(B, dim, Nb);
  Map<VectorXf> _avg(avg, dim);
  Map<ArrayXf> _scale_a(scale_a, Nb);
  Map<ArrayXf> _scale_b(scale_b, Nb);
  Map<MatrixXf> _result(result, Nb, N);

  _result = ((_B.transpose() * (_X.colwise() - _avg)).array().colwise() * _scale_a).colwise() + _scale_b;

  

  // for (float const *X_end = X + N * dim; X != X_end; X += dim) {
  //   float const *b = B;
  //   for (int j = 0; j < Nb; ++j) {
  //     float sum = 0.0;
  //     for (int k = 0; k < dim; ++k) {
  //       sum += (X[k] - avg[k]) * *b++;
  //     }
  //     *result++ = sum * scale_a[j] + scale_b[j];
  //   }
  // }

  // Try iterating over the basis in the outer loop?

  // GOOD
// #pragma omp parallel for schedule(static)
//   for (int i = 0; i < N; ++i) {
//     float const *x = X + i * dim;
//     float *res = result + i * Nb;

//     float const *b = B;
//     for (int j = 0; j < Nb; ++j) {
//       float sum = 0.0;
// #pragma omp simd reduction(+:sum)
//       for (int k = 0; k < dim; ++k) {
//         sum += (x[k] - avg[k]) * *b++;
//       }
//       res[j] = sum * scale_a[j] + scale_b[j];
//     }
//   }

  // float const *b = B;
  // for (int j = 0; j < Nb; ++j) {
  //   for (int i = 0; i < N; ++i) {
  //     float const *x = X + i * dim;
  //     float *res = result + i * Nb;

  //     float sum = 0.0;
  //     for (int k = 0; k < dim; ++k) {
  //       sum += (x[k] - avg[k]) * *b++;
  //     }
  //     res[j] = sum * scale_a[j] + scale_b[j];
  //   }
  // }
}
