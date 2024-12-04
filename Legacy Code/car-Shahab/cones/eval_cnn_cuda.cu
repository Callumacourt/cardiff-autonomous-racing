#include "mex.h"
#include <math.h>
#include "gpu/mxGPUArray.h"
#include <cuda_runtime_api.h>

#define MAX(a, b) (a > b ? a : b)

#define CHANNELS 4 // Channels in image texture
#define CONE_W 18
#define CONE_H 24

#define DIM (CONE_W * CONE_H * 3)

#define N1 8
typedef uint8_T byte;
byte const *im;
int w, h, d; // Size of image
texture<uchar4, cudaTextureType2D, cudaReadModeElementType> tex;

float const *B; // Box coordinates

__device__ __constant__ float F1[N1][3][5][5];
__device__ __constant__ float B1[N1];
// __device__ __constant__ float F1[N1][3][5][5];
// __device__ __constant__ float B1[N1];

// __device__ uchar4 get_pixel(const int row, const int col, const float left, const float top, const float ww, const float hh, const float scale_a, const float scale_b)
// {
//   // float scale_a = (float)(ww) / (float)(CONE_W); // TODO: Precompute
//   // float scale_b = (float)(hh) / (float)(CONE_H);
//   float x = left + (0.5f + col) * scale_a;
//   float y = top + (0.5f + row) * scale_b;// + col * scale_a;
//   return tex2D(tex, x, y);
// }

__global__
void eval_cnn(float * const result,
              float const * const B, unsigned int const N) {
  unsigned int const idx = blockIdx.x * blockDim.x + threadIdx.x;
  if (idx >= N) {
    return;
  }
  float left = B[4 * idx + 0] - 1.0;
  float top = B[4 * idx + 1] - 1.0;
  float ww = B[4 * idx + 2];
  float hh = B[4 * idx + 3];

  float scale_a = (float)(ww) / (float)(CONE_W); // TODO: Precompute
  float scale_b = (float)(hh) / (float)(CONE_H);

  // float out1[3][CONE_W][CONE_H];
  // for (int col = 0; col < CONE_W; ++col) {
  //   float x = left + (0.5f + col) * scale_a;
  //   for (int row = 0; row < CONE_H; ++row) {
  //     float y = top + (0.5f + row) * scale_b;
  //     uchar4 c = tex2D(tex, x, y);

  //     out1[0][col][row] = (float)c.x;
  //     out1[1][col][row] = (float)c.y;
  //     out1[2][col][row] = (float)c.z;
  //   }
  // }


  float out2[N1][CONE_W / 3][CONE_H / 3];
  int pos = idx * 8 * 6 * 8;

  for (int filter = 0; filter < 8; ++filter) {
    for (int col = 0; col < 6; ++col) {
      for (int row = 0; row < 8; ++row) {

        float max_val = -10e6;
        // Max pooling
        for (int pool_col = 0; pool_col < 3; ++pool_col) {
          for (int pool_row = 0; pool_row < 3; ++pool_row) {

            // Convolution
            float total = 0.0; // Convolution total
            for (int dcol_conv = 0; dcol_conv < 5; ++dcol_conv) {
              int imc = col * 3 + pool_col + dcol_conv - 2;
                float x = left + (0.5f + imc) * scale_a;
              for (int drow_conv = 0; drow_conv < 5; ++drow_conv) {
                int imr = row * 3 + pool_row + drow_conv - 2;
                if (imr >= 0 && imc >= 0 && imr < CONE_H && imc < CONE_W) {
                float y = top + (0.5f + imr) * scale_b;// + col * scale_a;
                uchar4 pixel = tex2D(tex, x, y);//get_pixel(imr, imc, left, top, ww, hh, scale_a, scale_b);

                total +=
                  (float)pixel.x * F1[filter][0][dcol_conv][drow_conv] +
                  (float)pixel.y * F1[filter][1][dcol_conv][drow_conv] +
                  (float)pixel.z * F1[filter][2][dcol_conv][drow_conv];
              }
            }
            }

            max_val = MAX(max_val, total + B1[filter]); // TODO: Check if there is a CUDA primitive
          }
        }



        out2[filter][col][row] = MAX(0.0, max_val); //compute_out2(filter, row, col, out1);
        result[pos++] = out2[filter][col][row];
      }
    }
  }



  
}




void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {

  mxInitGPU();

  if (4 != nrhs) {
    mexErrMsgTxt("Expected four arguments.\n");
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

  // Layer 1 filters
  mxArray const* F1_ = prhs[2];
  float * F1__ = (float*)mxGetData(F1_);
  cudaMemcpyToSymbol(F1, F1__, 5 * 5 * 3 * N1 * sizeof(float));

  // Layer 1 biases
  mxArray const* B1_ = prhs[3];
  float * B1__ = (float*)mxGetData(B1_);
  cudaMemcpyToSymbol(B1, B1__, N1 * sizeof(float));


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
  dims_out[0] = CONE_H / 3; dims_out[1] = CONE_W / 3; dims_out[2] = N1; dims_out[3] = Bdims[1];
  mxGPUArray * const result_gpu_ = mxGPUCreateGPUArray(4, dims_out, mxSINGLE_CLASS, mxREAL, MX_GPU_INITIALIZE_VALUES);
  float * const result_gpu = static_cast<float *>(mxGPUGetData(result_gpu_));

  int const threadsPerBlock = 256;
  int blocksPerGrid;
  int N = Bdims[1];
  blocksPerGrid = (N + threadsPerBlock - 1) / threadsPerBlock;
  eval_cnn<<<blocksPerGrid, threadsPerBlock>>>(result_gpu, B_gpu, N);

  // Output
  plhs[0] = mxGPUCreateMxArrayOnGPU(result_gpu_);

  cudaUnbindTexture(tex);
  cudaFree(im_gpu_data);
  // mxGPUDestroyGPUArray(im_gpu_);
  mxGPUDestroyGPUArray(result_gpu_);
  mxGPUDestroyGPUArray(B_gpu_);
}
