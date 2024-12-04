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
    if (nrhs != 3)
    {
        mexErrMsgTxt("Expected five arguments.\n");
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
    
    
    mxArray const *template_ = prhs[2];
    byte * temp = (byte *)mxGetData(template_);
    
    plhs[0] = mxCreateNumericMatrix(nmodels, nrows * ncols, mxDOUBLE_CLASS, mxREAL);
    double * result_prob = (double *)mxGetData(plhs[0]);
    double * result_prob_start = result_prob;
    plhs[1] = mxCreateNumericMatrix(nrows * ncols, nmodels, mxDOUBLE_CLASS, mxREAL);
    double * C = (double *)mxGetData(plhs[1]);

    std::vector<double> mean(nmodels);
    std::vector<double> std(nmodels);
    int n = 1;
    for (byte *i = im, *i_end = i + ncols * nrows; i != i_end; ++i, ++n)
    {
        if (*temp++)
        {
            int index = *i << 16 | *(i + pitch) << 8 | *(i + 2 * pitch);
            
            for (int j = 0; j < nmodels; ++j)
            {
                double p = prob[j * PROB_PITCH + index];
                *result_prob++ = p;
                
                double prev_mean = mean[j];
                mean[j] += (p - mean[j]) / (double)n;
                std[j] += (p - mean[j]) * (p - prev_mean);
            }
        }
        else
        {
            result_prob += nmodels;
            for (int j = 0; j < nmodels; ++j)
            {
                double prev_mean = mean[j];
                mean[j] -= mean[j] / (double)n;
                std[j] += mean[j] * prev_mean;
            }
        }
    }
    
    // Find which of the models is most likely, for each pixel
    double * p = result_prob_start;
    std::vector<int> argmax(pitch);
    for (std::vector<int>::iterator j = argmax.begin(); j != argmax.end(); ++j)
    {
        double max_p = -1e10;
        int idx = 0;                
        for (int i = 0; i < nmodels; ++i, ++p)
        {
            if (*p > max_p)
            {
                max_p = *p;
                idx = i;
            }
        }
        *j = idx;
    }
    
    
    p = result_prob_start;
    for (int i = 0; i < nmodels; ++i)
    {
        double mean_i = mean[i];
        double std_i = sqrt(std[i] / (double)pitch);
        double threshold = mean_i + 2.0 * std_i;
//         mexPrintf("mean = %f, std = %f, threshold = %f\n\n", mean_i, std_i, threshold);
        for (int j = 0; j < pitch; ++j, ++C)
        {
            if (p[j * nmodels + i] > threshold && i == argmax[j])
            {
                *C = 1;
            }
        }
        
        
        //mexPrintf("mean = %f, std = %f\n", mean[i], std[i]);
    }
    
    
//     mxArray const *start_ = prhs[1];
//     double* start = (double*)mxGetData(start_);
//     mxArray const *end_ = prhs[2];
//     double* end = (double*)mxGetData(end_);
    
    
}
