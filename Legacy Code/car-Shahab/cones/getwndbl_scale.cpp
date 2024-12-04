#include "mex.h"
#include <math.h>
// #include "optmath.h"

// #define d2i(x) (ftoi(x))

int w, h, d, texw, texh, texd;

typedef unsigned char byte;

float *buf;
byte *tex;
int bufpitch;
int texpitch;

double top;
double left;
double width;
double height;

#define MIN(a, b) (a < b ? a : b)
#define MAX(a, b) (a > b ? a : b)

void getwnd_gray() {
  float *dest = buf;
  // fpu_control fpu;
  // fpu_setround(&fpu);
  double scale_b = (double)(width) / (double)(w);
  double scale_a = (double)(height) / (double)(h);

  if (left >= 0 && top >= 0 && ceil(left + width) <= texw && ceil(top + height) <= texh) {
    double v = left + 0.5 * scale_b - 0.5;
    for (int col = 0; col < w; ++col) {
      int iv = int(v);
      double fv = v - (double)iv;
      int A = iv * texh;
      int B = A + texh;

      double u = top + 0.5 * scale_a - 0.5;
      for (int row = 0; row < h; ++row) {
        int iu = int(u);
        double fu = u - (double)iu;

        double c1, c2;
	int a = tex[A + iu];
	int b = tex[A + iu + 1];
        c1 = a + ((int)tex[B + iu] - a) * fv;
        c2 = b + ((int)tex[B + iu + 1] - b) * fv;
        *dest = (c1 + (c2 - c1) * fu);
        ++dest;
        u += scale_a;
      }
      v += scale_b;
    }
  }
  else {
    double v = left + 0.5 * scale_b - 0.5;
    for (int col = 0; col < w; ++col) {
      int iv = floor(v);
      double fv = v - (double)iv;
      int A = MAX(0, MIN(iv, texw-1)) * texh;
      int B = MAX(0, MIN(iv+1, texw-1)) * texh;

      double u = top + 0.5 * scale_a - 0.5;
      for (int row = 0; row < h; ++row) {
        int iu = floor(u);
        double fu = u - (double)iu;
        int oful = A + MAX(0, MIN(iu, texh-1));
        int ofur = A + MAX(0, MIN(iu+1, texh-1));
        int ofdl = B + MAX(0, MIN(iu, texh-1));
        int ofdr = B + MAX(0, MIN(iu+1, texh-1));


        double c1, c2;
        c1 = tex[oful] + ((int)tex[ofdl] - (int)tex[oful]) * fv;
        c2 = tex[ofur] + ((int)tex[ofdr] - (int)tex[ofur]) * fv;
        *dest = (c1 + (c2 - c1) * fu);
        ++dest;
        u += scale_a;
      }
      v += scale_b;
    }
  }
  // fpu_restore(fpu);
}

void getwnd_rgb() {
  texpitch = texw * texh;
  bufpitch = h * w;

  byte *texr = tex;
  byte *texg = tex + texpitch;
  byte *texb = tex + texpitch * 2;
  // fpu_control fpu;
  // fpu_setround(&fpu);
  double scale_b = (double)(width) / (double)(w);
  double scale_a = (double)(height) / (double)(h);

  if (left >= 0 && top >= 0 && ceil(left + width) <= texw && ceil(top + height) <= texh) {
    // Fast case with no checks
    
#pragma omp parallel for schedule(static)
    for (int col = 0; col < w; ++col) {
      double v = left + 0.5 * scale_b - 0.5 + (scale_b * col);
      int iv = int(v);
      double fv = v - (double)iv;
      int A = iv * texh;
      int B = A + texh;
      float *destr = buf + col * h;
      float *destg = destr + bufpitch;
      float *destb = destg + bufpitch;

      double u = top + 0.5 * scale_a - 0.5;
      for (int row = 0; row < h; ++row) {
        int iu = int(u);
        double fu = u - (double)iu;

	int Biu = B + iu;
        double c1, c2;
	int a = texr[A + iu];
	int b = texr[A + iu + 1];
        c1 = a + ((int)texr[Biu] - a) * fv;
        c2 = b + ((int)texr[Biu + 1] - b) * fv;
        *destr = (c1 + (c2 - c1) * fu);

 	a = texg[A + iu];
	b = texg[A + iu + 1];
        c1 = a + ((int)texg[Biu] - a) * fv;
        c2 = b + ((int)texg[Biu + 1] - b) * fv;
        *destg = (c1 + (c2 - c1) * fu);

	a = texb[A + iu];
	b = texb[A + iu + 1];
        c1 = a + ((int)texb[Biu] - a) * fv;
        c2 = b + ((int)texb[Biu + 1] - b) * fv;
        *destb = (c1 + (c2 - c1) * fu);

        ++destr;
	++destg;
	++destb;
        u += scale_a;
      }
      // v += scale_b;
    }
  }
  else {
    // Slow case with checks
    float *destr = buf;
    float *destg = buf + bufpitch;
    float *destb = buf + bufpitch * 2;
    double v = left + 0.5 * scale_b - 0.5;
    for (int col = 0; col < w; ++col) {
      int iv = floor(v);
      double fv = v - (double)iv;
      int A = MAX(0, MIN(iv, texw-1)) * texh;
      int B = MAX(0, MIN(iv+1, texw-1)) * texh;

      double u = top + 0.5 * scale_a - 0.5;
      for (int row = 0; row < h; ++row) {
        int iu = floor(u);
        double fu = u - (double)iu;
        int oful = A + MAX(0, MIN(iu, texh-1));
        int ofur = A + MAX(0, MIN(iu+1, texh-1));
        int ofdl = B + MAX(0, MIN(iu, texh-1));
        int ofdr = B + MAX(0, MIN(iu+1, texh-1));


        double c1, c2;
        c1 = texr[oful] + ((int)texr[ofdl] - (int)texr[oful]) * fv;
        c2 = texr[ofur] + ((int)texr[ofdr] - (int)texr[ofur]) * fv;
        *destr = (c1 + (c2 - c1) * fu);

        c1 = texg[oful] + ((int)texg[ofdl] - (int)texg[oful]) * fv;
        c2 = texg[ofur] + ((int)texg[ofdr] - (int)texg[ofur]) * fv;
        *destg = (c1 + (c2 - c1) * fu);

	c1 = texb[oful] + ((int)texb[ofdl] - (int)texb[oful]) * fv;
        c2 = texb[ofur] + ((int)texb[ofdr] - (int)texb[ofur]) * fv;
        *destb = (c1 + (c2 - c1) * fu);

	++destr;
	++destg;
	++destb;
	
        u += scale_a;
      }
      v += scale_b;
    }
  }
  // fpu_restore(fpu);
}


void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {

  if (6 != nrhs)
    {
      mexErrMsgTxt("Expected six arguments.\n");
      return;
    }

  mxArray const* buf_ = prhs[0];
  mwSize const* bufdims = mxGetDimensions(buf_);
  h = bufdims[0]; w = bufdims[1]; //d = bufdims[2];
  buf = (float*)mxGetData(buf_);

  mxArray const* tex_ = prhs[1];
  mwSize const* texdims = mxGetDimensions(tex_);
  texh = texdims[0]; texw = texdims[1];
  if (mxGetNumberOfDimensions(tex_) < 3)
    texd = 1;
  else
    texd = texdims[2];
  tex = (byte*)mxGetData(tex_);

  mxArray const* left_ = prhs[2];
  left = *((double*)mxGetData(left_)) - 1;

  mxArray const* top_ = prhs[3];
  top = *((double*)mxGetData(top_)) - 1;

  mxArray const* width_ = prhs[4];
  width = *((double*)mxGetData(width_));

  mxArray const* height_ = prhs[5];
  height = *((double*)mxGetData(height_));

  if (1 == texd) {
    getwnd_gray();
  }
  else {
    getwnd_rgb();
  }
}
