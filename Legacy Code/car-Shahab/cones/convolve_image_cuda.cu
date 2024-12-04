#include "mex.h"
#include <math.h>
#include "gpu/mxGPUArray.h"
#include <cuda_runtime_api.h>

#define N1 8
typedef uint8_T byte;
// texture<uchar4, cudaTextureType2D, cudaReadModeElementType> tex;

float const *B; // Box coordinates

__device__ __constant__ float F1[N1][3][5][5];
__device__ __constant__ float B1[N1];

unsigned int iDivUp( const unsigned int &a, const unsigned int &b ) { return ( a%b != 0 ) ? (a/b+1):(a/b); }

__global__
void convolve(float * const result,
              byte const * const im, unsigned int const h, unsigned int const w) {
  const unsigned int col = blockIdx.x * blockDim.x + threadIdx.x;
  const unsigned int row = blockIdx.y * blockDim.y + threadIdx.y;
  if (col >= w || row >= h) {
    return;
  }

  for(int filter = 0; filter < N1; ++filter) {
    float total = 0.0f;
    for (int fcol = 0; fcol < 5; ++fcol) {
      for (int frow = 0; frow < 5; ++frow) {
        int pos = (row + frow) * w * 3 + (col + fcol) * 3;
        total += F1[filter][0][fcol][frow] * im[pos] +
          F1[filter][1][fcol][frow] * im[pos + 1] +
          F1[filter][2][fcol][frow] * im[pos + 2];
     // total += (float)im[pos];// + im[pos + 1] + im[pos + 2];
      }
    }
  // result[col * h + row] = row;
    result[col * h + row + (w * h * filter)] = total;//im[row * w * 3 + col * 3];
  }
}



void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {

  mxInitGPU();

  if (3 != nrhs) {
    mexErrMsgTxt("Expected three arguments.\n");
    return;
  }

  // Image
  byte const *im;
  mxArray const* im_ = prhs[0];
  mwSize const* im_dims = mxGetDimensions(im_);
  int w, h, d; // Size of image
  h = im_dims[0]; w = im_dims[1]; d = im_dims[2];
  im = (unsigned char const*)mxGetData(im_);

  // Layer 1 filters
  mxArray const* F1_ = prhs[1];
  float * F1__ = (float*)mxGetData(F1_);
  cudaMemcpyToSymbol(F1, F1__, 5 * 5 * 3 * N1 * sizeof(float));

  // Layer 1 biases
  mxArray const* B1_ = prhs[2];
  float * B1__ = (float*)mxGetData(B1_);
  cudaMemcpyToSymbol(B1, B1__, N1 * sizeof(float));


  // mxGPUArray * const im_gpu_ = mxGPUCreateGPUArray(3, im_dims,
  //                                                  mxUINT8_CLASS, mxREAL,
  //                                                  MX_GPU_DO_NOT_INITIALIZE);
  // byte * const im_gpu = static_cast<byte *>(mxGPUGetData(im_gpu_));
  // cudaMemcpy(im_gpu, im, im_dims[0] * im_dims[1] * im_dims[3] * sizeof(byte), cudaMemcpyHostToDevice);
  mwSize dims_in[3];
  dims_in[0] = h; dims_in[1] = w; dims_in[2] = d;

  mxGPUArray * const im_gpu_ = mxGPUCreateGPUArray(3, dims_in,
                                                   mxUINT8_CLASS, mxREAL,
                                                   MX_GPU_DO_NOT_INITIALIZE);

  byte * const im_gpu = static_cast<byte *>(mxGPUGetData(im_gpu_));
  cudaMemcpy(im_gpu, im, h*w*d*sizeof(byte), cudaMemcpyHostToDevice);



  mwSize dims_out[3];
  dims_out[0] = im_dims[0]; dims_out[1] = im_dims[1]; dims_out[2] = N1;
  mxGPUArray * const result_gpu_ = mxGPUCreateGPUArray(3, dims_out, mxSINGLE_CLASS, mxREAL, MX_GPU_INITIALIZE_VALUES);
  float * const result_gpu = static_cast<float *>(mxGPUGetData(result_gpu_));



  // int const threadsPerBlock = 256;
  // int blocksPerGrid;
  // int N = Bdims[1];
  // blocksPerGrid = (N + threadsPerBlock - 1) / threadsPerBlock;

  int blockW = 32;
  int blockH = 32;
  const dim3 grid( iDivUp( im_dims[1], blockW ), iDivUp( im_dims[0], blockH ) );
  const dim3 threadBlock( blockW, blockH );

  convolve<<<grid, threadBlock>>>(result_gpu, im_gpu, im_dims[0], im_dims[1]);
  cudaDeviceSynchronize();

  // Output
  plhs[0] = mxGPUCreateMxArrayOnGPU(result_gpu_);

  // cudaUnbindTexture(tex);
  // cudaFree(im_gpu_data);
  mxGPUDestroyGPUArray(im_gpu_);
  // mxGPUDestroyGPUArray(result_gpu_);
  // mxGPUDestroyGPUArray(B_gpu_);
}
