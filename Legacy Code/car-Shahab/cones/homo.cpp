#include "math.h"
#include "mex.h"
#include <cstring>
typedef unsigned char byte;

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {
    if (1 != nrhs) {
        mexErrMsgTxt("Expected one argument.\n");
        return;
    }
    
    mxArray const *x_ = prhs[0];
    double* x = (double*)mxGetData(x_);
    int ncols = mxGetN(x_);
    int nrows = mxGetM(x_);
    
    int numel = mxGetNumberOfElements(x_);
    
    plhs[0] = mxCreateNumericMatrix(nrows + 1, ncols, mxDOUBLE_CLASS, mxREAL);

    if (0 == numel) {
        return;
    }

    double* dst = (double*)mxGetData(plhs[0]);
    for (int i = 0; i < ncols; ++i)
    {
        for (int j = 0; j < nrows; ++j)
            *dst++ = *x++;
        *dst++ = 1.0;
    }
}
