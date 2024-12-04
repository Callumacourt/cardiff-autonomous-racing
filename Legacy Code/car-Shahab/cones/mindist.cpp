#include "mex.h"
#include <limits>
#include <math.h>

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) {
    if (2 != nrhs) {
        mexErrMsgTxt("Expected two arguments.\n");
        return;
    }
    
    mxArray const* x_ = prhs[0];
    mxArray const* y_ = prhs[1];
    
    if (!mxIsDouble(x_) || !mxIsDouble(y_)) {
        mexErrMsgTxt("X and Y must be of type double.\n");
        return;
    }
    int x_rows = mxGetM(x_); int x_cols = mxGetN(x_);
    int y_rows = mxGetM(y_); int y_cols = mxGetN(y_);
    
    if ((x_rows != y_rows) || (x_rows != 2))  {
        mexErrMsgTxt("X and Y must be 2-by-N matrices.\n");
        return;
    }
    
    plhs[0] = mxCreateNumericMatrix(1, 1, mxDOUBLE_CLASS, mxREAL);
    double * result = (double*)mxGetData(plhs[0]);
    double *y0 = (double*)mxGetData(y_);
    double *x = (double*)mxGetData(x_);
    double mind = 1e99;//std::numeric_limits<double>::max();
    for (double *x_end = x + 2 * x_cols; x != x_end; x += 2)
    {
        double *y = y0;
        for (double *y_end = y + 2 * y_cols; y != y_end; y += 2)
        {
            double d0 = x[0] - y[0];
            double d1 = x[1] - y[1];
            double d = d0 * d0 + d1 * d1;
            if (d < mind)
                mind = d;
        }
    }
    *result = sqrt(mind);
}
