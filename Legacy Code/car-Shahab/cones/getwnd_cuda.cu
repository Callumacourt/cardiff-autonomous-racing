#include "mex.h"
#include <math.h>
#include "gpu/mxGPUArray.h"
#include <cuda_runtime_api.h>

#define CHANNELS 4 // Channels in image texture
#define CONE_W 18
#define CONE_H 24

#define DIM (CONE_W * CONE_H * 3)

typedef uint8_T byte;
byte const *im;
int w, h, d; // Size of image
texture<uchar4, cudaTextureType2D, cudaReadModeElementType> tex;

float const *B; // Box coordinates

__device__ uchar4 get_pixel(const int row, const int col, const float left, const float top, const float ww, const float hh)
{
  float scale_a = (float)(ww) / (float)(CONE_W); // TODO: Precompute
  float scale_b = (float)(hh) / (float)(CONE_H);
  float x = left + (0.5f + col) * scale_a;
  float y = top + (0.5f + row) * scale_b;// + col * scale_a;
  return tex2D(tex, x, y);
}

__global__
void getwnd(float * const result,
            float const * const B, unsigned int const N) {
  unsigned int const idx = blockIdx.x * blockDim.x + threadIdx.x;
  if (idx >= N) {
    return;
  }
  float left = B[4 * idx + 0] - 1.0;
  float top = B[4 * idx + 1] - 1.0;
  float ww = B[4 * idx + 2];
  float hh = B[4 * idx + 3];
  int pos = 0;
  for (int col = 0; col < CONE_W; ++col) {
    for (int row = 0; row < CONE_H; ++row) {
      uchar4 c = get_pixel(row, col, left, top, ww, hh);
      result[idx * DIM + pos] = (float)c.x;
      result[idx * DIM + pos + CONE_W * CONE_H] = (float)c.y;
      result[idx * DIM + pos + CONE_W * CONE_H * 2] = (float)c.z;
      ++pos;
    }
  }
}




void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {

  mxInitGPU();

  if (2 != nrhs) {
    mexErrMsgTxt("Expected two arguments.\n");
    return;
  }

  // Image
  mxArray const* im_ = prhs[0];
  mwSize const* im_dims = mxGetDimensions(im_);
  h = im_dims[0]; w = im_dims[1]; d = im_dims[2];
  im = (unsigned char const*)mxGetData(im_);

  // Box coordinates
  mxArray const* B_ = prhs[1];
  mwSize const* Bdims = mxGetDimensions(prhs[1]);
  // Nb = Bdims[1];
  B = (float const*)mxGetData(B_);

  int threads_w = 20;
  int threads_h = 8;

  // Compute the thread block and grid sizes based on the board dimensions.
  int blocksPerGridH = (h + threads_h - 1) / threads_h;
  int blocksPerGridW = (w + threads_w - 1) / threads_w;
  // mexPrintf("blocks: %d x %d\n", blocksPerGridH, blocksPerGridW);
  dim3 dimBlock(blocksPerGridH, blocksPerGridW);
  dim3 dimThread(threads_h, threads_w);

  size_t pitch;
  byte *im_gpu_data;
  cudaMallocPitch((void**)&im_gpu_data, &pitch, CHANNELS * w * sizeof(byte), h);
  cudaChannelFormatDesc desc = cudaCreateChannelDesc<uchar4>();
  cudaMemcpy2D(im_gpu_data, pitch, im, CHANNELS * w, CHANNELS * w, h, cudaMemcpyHostToDevice);
  cudaBindTexture2D(0, tex, im_gpu_data, desc, w, h, pitch);




  mxGPUArray * const B_gpu_ = mxGPUCreateGPUArray(2, Bdims,
                                                  mxSINGLE_CLASS, mxREAL,
                                                  MX_GPU_DO_NOT_INITIALIZE);
  float * const B_gpu = static_cast<float *>(mxGPUGetData(B_gpu_));
  cudaMemcpy(B_gpu, B, Bdims[0] * Bdims[1] * sizeof(float), cudaMemcpyHostToDevice);

  mwSize dims_out[4];
  dims_out[0] = CONE_H; dims_out[1] = CONE_W; dims_out[2] = 3; dims_out[3] = Bdims[1];
  mxGPUArray * const result_gpu_ = mxGPUCreateGPUArray(4, dims_out, mxSINGLE_CLASS, mxREAL, MX_GPU_INITIALIZE_VALUES);
  float * const result_gpu = static_cast<float *>(mxGPUGetData(result_gpu_));

  int const threadsPerBlock = 256;
  int blocksPerGrid;
  int N = Bdims[1];
  blocksPerGrid = (N + threadsPerBlock - 1) / threadsPerBlock;
  getwnd<<<blocksPerGrid, threadsPerBlock>>>(result_gpu, B_gpu, N);

  // Output
  plhs[0] = mxGPUCreateMxArrayOnGPU(result_gpu_);

  cudaUnbindTexture(tex);
  cudaFree(im_gpu_data);
  // mxGPUDestroyGPUArray(im_gpu_);
  mxGPUDestroyGPUArray(result_gpu_);
  mxGPUDestroyGPUArray(B_gpu_);
}
