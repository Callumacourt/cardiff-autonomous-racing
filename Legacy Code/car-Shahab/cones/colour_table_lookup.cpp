#include "mex.h"
#include <math.h>
#include <vector>
typedef unsigned char byte;

byte* im;

int nrows, ncols, pitch;



#define PROB_PITCH 16777216
void mexFunction(int nlhs, mxArray *plhs[], int nrhs,
        const mxArray *prhs[])
{
    if (nrhs != 2)
    {
        mexErrMsgTxt("Expected two arguments.\n");
    }
    
    mxArray const *im_ = prhs[0];
    const mwSize* dims = mxGetDimensions(im_);
    mwSize ndims = mxGetNumberOfDimensions(im_);
    
    mxClassID category = mxGetClassID(im_);
    if (mxUINT8_CLASS != category) {
        mexErrMsgTxt("Expected an 8-bit image.\n");
    }
    
    im = (byte*)mxGetData(im_);
    nrows = dims[0];
    ncols = dims[1];
    pitch = nrows * ncols;
    
    mxArray const *prob_ = prhs[1];
    int nmodels = mxGetN(prob_);
    double * prob = (double *)mxGetData(prob_);
//     mexPrintf("nmodels = %d\n", nmodels);
    
    
    
    plhs[0] = mxCreateNumericMatrix(nmodels, nrows * ncols, mxDOUBLE_CLASS, mxREAL);
    double * result_prob = (double *)mxGetData(plhs[0]);
    
    int n = 1;
    for (byte *i = im, *i_end = i + ncols * nrows; i != i_end; ++i, ++n)
    {
        int index = *i << 16 | *(i + pitch) << 8 | *(i + 2 * pitch);
        for (int j = 0; j < nmodels; ++j)
        {
            *result_prob++ = prob[j * PROB_PITCH + index];
        }
    }
}
