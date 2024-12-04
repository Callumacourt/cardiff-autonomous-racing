#include "mex.h"
#include <math.h>
#include "gpu/mxGPUArray.h"
#include <cuda_runtime_api.h>

// Project onto AM basis and apply linear transform, then score the result with SVM.

#define SQUARE(x) ((x) * (x))
#define MIN(a, b) (a < b ? a : b)
#define MAX(a, b) (a > b ? a : b)

#define CONE_W 21
#define CONE_H 26
#define DIM (CONE_H * CONE_W * 3)
#define NB 8
#define NV 20
#define CHANNELS 4
// __device__ __constant__ float vectors[NV * NB];
// __device__ __constant__ float alphas[NV];
// __device__ __constant__ float bias;
// __device__ __constant__ float scale;



typedef uint8_T byte;
byte const *im;
float const *B;

texture<uchar4, cudaTextureType2D, cudaReadModeElementType> tex;


int w, h, d; // Size of image
// int dim; // Dimensionality of data
// int Nb;  // Number of basis vectors
// int Nv;  // Number of support vectors (and alphas)



__global__
void am_svm(float * const result,
          int const imh,
          int const imw,
          float const * const B,
          float const * const vectors,
          float const * const alphas,
          float const bias,
          float const scale,
	  float const ww,
	  float const hh          )
{
  // Coordinates for this thread within the board
  unsigned int const imrow = blockIdx.x * blockDim.x + threadIdx.x;
  unsigned int const imcol = blockIdx.y * blockDim.y + threadIdx.y;


  // Only threads inside the grid need to compute a result
  if ((imrow < imh) && (imcol < imw)) {
    float proj[NB];
    for (int i = 0; i < NB; ++i) {
      proj[i] = 0.0f;
    }

    // Sampling and projection
    // float ww = CONE_W;
    // float hh = CONE_H;
    float left = (float)imcol - (ww - 1.0) * 0.5f;
    float top = (float)imrow - (hh - 1.0) * 0.5f;
    float scale_a = (float)(ww) / (float)(CONE_W);
    float scale_b = (float)(hh) / (float)(CONE_H);

    for (int row = 0; row < CONE_H; ++row) {
      float y = top + (0.5f + row) * scale_b;
      float x = left + 0.5f * scale_a;// + col * scale_a;
      for (int col = 0; col < CONE_W; ++col, x += scale_a) {
        uchar4 c = tex2D(tex, x, y);
        float const * b = B + (col * CONE_H + row) * 3;
        for (int j = 0; j < NB; ++j, b += CONE_W * CONE_H * 3) {
          proj[j] += b[0] * c.x + b[1] * c.y + b[2] * c.z;
        }
      }
    }


    // Prediction
    float res = bias;
    float const *v = vectors;
    for (int i = 0; i < NV; ++i) {
      float sum = 0.0;
      for (int j = 0; j < NB; ++j) {
        float diff = proj[j] - *v++;
        sum += diff * diff;
      }
      res += alphas[i] * __expf(-sum * scale);
    }

    result[imrow + imcol * imh] = max(result[imrow + imcol * imh], res);
    // result[imrow + imcol * imh] = proj[3];


  }
}

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {

  mxInitGPU();

  if (10 != nrhs) {
    mexErrMsgTxt("Expected six arguments.\n");
    return;
  }

  // Image
  mxArray const* im_ = prhs[0];
  mwSize const* im_dims = mxGetDimensions(im_);
  h = im_dims[0]; w = im_dims[1]; d = im_dims[2];
  im = (unsigned char const*)mxGetData(im_);

  // Basis vectors
  mxArray const* B_ = prhs[1];
  mwSize const* Bdims = mxGetDimensions(prhs[1]);
  // Nb = Bdims[1];
  B = (float const*)mxGetData(B_);

  // // Support vectors
  mxArray const* vectors_ = prhs[2];
  mwSize const* vecdims = mxGetDimensions(vectors_);
  // Nv = vecdims[1];
  float * vectors__ = (float*)mxGetData(vectors_);


  // Alphas
  mxArray const* alphas_ = prhs[3];
  float * alphas__ = (float*)mxGetData(alphas_);
  mwSize const* alphadims = mxGetDimensions(alphas_);

  // Bias
  mxArray const* bias_ = prhs[4];
  float bias__ = *((float*)mxGetData(bias_));

  // Scale
  mxArray const* scale_ = prhs[5];
  float scale__ = *((float*)mxGetData(scale_));

  // blocks_w
  // int threads_w = *((double*)mxGetData(prhs[6]));

  // blocks_h
  // int threads_h = *((double*)mxGetData(prhs[7]));

  // ww
  mxArray const* ww_ = prhs[8];
  double * ww = (double*)mxGetData(ww_);
  mwSize const* wwdims = mxGetDimensions(ww_);

  // hh
  mxArray const* hh_ = prhs[9];
  double * hh = (double*)mxGetData(hh_);
  mwSize const* hhdims = mxGetDimensions(hh_);

  int Nsizes = wwdims[0] * wwdims[1];

  int threads_w = 20;
  int threads_h = 8;
  
  // Compute the thread block and grid sizes based on the board dimensions.
  int blocksPerGridH = (h + threads_h - 1) / threads_h;
  int blocksPerGridW = (w + threads_w - 1) / threads_w;
  // mexPrintf("blocks: %d x %d\n", blocksPerGridH, blocksPerGridW);
  dim3 dimBlock(blocksPerGridH, blocksPerGridW);
  dim3 dimThread(threads_h, threads_w);

  // return;

  // cudaMemcpyToSymbol(vectors, vectors__, NV * NB * sizeof(float));
  // cudaMemcpyToSymbol(alphas, alphas__, NV * sizeof(float));
  // cudaMemcpyToSymbol(bias, &bias__, sizeof(float));
  // cudaMemcpyToSymbol(scale, &scale__, sizeof(float));



  mwSize dims_in[3];
  dims_in[0] = h; dims_in[1] = w; dims_in[2] = d;

  // mxGPUArray * const im_gpu_ = mxGPUCreateGPUArray(3, dims_in,
  // mxUINT8_CLASS, mxREAL,
  // MX_GPU_DO_NOT_INITIALIZE);

  // uint8_T * const im_gpu = static_cast<uint8_T *>(mxGPUGetData(im_gpu_));
  // cudaMemcpy(im_gpu, im, h*w*d*sizeof(uint8_T), cudaMemcpyHostToDevice);

  size_t pitch;
  byte *im_gpu_data;
  cudaMallocPitch((void**)&im_gpu_data, &pitch, CHANNELS * w * sizeof(byte), h);
  cudaChannelFormatDesc desc = cudaCreateChannelDesc<uchar4>();
  // cudaMemcpy(im_gpu_data, im, h*w*4*sizeof(uint8_T), cudaMemcpyHostToDevice);
  cudaMemcpy2D(im_gpu_data, pitch, im, CHANNELS * w, CHANNELS * w, h, cudaMemcpyHostToDevice);
  cudaBindTexture2D(0, tex, im_gpu_data, desc, w, h, pitch);
  // mexPrintf("%d\n", pitch);



  mxGPUArray * const B_gpu_ = mxGPUCreateGPUArray(2, Bdims,
                                                  mxSINGLE_CLASS, mxREAL,
                                                  MX_GPU_DO_NOT_INITIALIZE);
  float * const B_gpu = static_cast<float *>(mxGPUGetData(B_gpu_));
  // mexPrintf("%d %d\n", Bdims[0], Bdims[1]);
  cudaMemcpy(B_gpu, B, Bdims[0] * Bdims[1] * sizeof(float), cudaMemcpyHostToDevice);


  mxGPUArray * const result_gpu_ = mxGPUCreateGPUArray(2, dims_in, mxSINGLE_CLASS, mxREAL, MX_GPU_INITIALIZE_VALUES);
  float * const result_gpu = static_cast<float *>(mxGPUGetData(result_gpu_));

  // Vectors
  mxGPUArray * const vectors_gpu_ = mxGPUCreateGPUArray(2, vecdims, mxSINGLE_CLASS, mxREAL, MX_GPU_DO_NOT_INITIALIZE);
  float * const vectors_gpu = static_cast<float *>(mxGPUGetData(vectors_gpu_));
  cudaMemcpy(vectors_gpu, vectors__, vecdims[0] * vecdims[1] * sizeof(float), cudaMemcpyHostToDevice);

  mxGPUArray * const alphas_gpu_ = mxGPUCreateGPUArray(2, alphadims, mxSINGLE_CLASS, mxREAL, MX_GPU_DO_NOT_INITIALIZE);
  float * const alphas_gpu = static_cast<float *>(mxGPUGetData(alphas_gpu_));
  cudaMemcpy(alphas_gpu, alphas__, alphadims[0] * alphadims[1] * sizeof(float), cudaMemcpyHostToDevice);






  for (int i = 0; i < Nsizes; ++i) {
    am_svm<<<dimBlock, dimThread>>>(result_gpu, h, w, B_gpu, vectors_gpu, alphas_gpu, bias__, scale__, ww[i], hh[i]);
  }


  // Output
  plhs[0] = mxCreateNumericMatrix(h, w, mxSINGLE_CLASS, mxREAL);
  float *result = (float*)mxGetData(plhs[0]);

  cudaMemcpy(result, result_gpu, h*w*sizeof(float), cudaMemcpyDeviceToHost);

  cudaUnbindTexture(tex);
  cudaFree(im_gpu_data);
  // mxGPUDestroyGPUArray(im_gpu_);
  mxGPUDestroyGPUArray(result_gpu_);
  mxGPUDestroyGPUArray(B_gpu_);
  mxGPUDestroyGPUArray(vectors_gpu_);
  mxGPUDestroyGPUArray(alphas_gpu_);
}

// TODO: B also to tex?
