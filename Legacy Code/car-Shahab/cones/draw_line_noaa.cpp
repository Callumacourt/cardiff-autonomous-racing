#include "mex.h"
#include <math.h>
typedef unsigned char byte;

const int INSIDE = 0; // 0000
const int LEFT = 1;   // 0001
const int RIGHT = 2;  // 0010
const int BOTTOM = 4; // 0100
const int TOP = 8;    // 1000

// Compute the bit code for a point (x, y) using the clip rectangle
// bounded diagonally by (1.0, 1.0), and (xmax, ymax)

// ASSUME THAT xmax, 1.0, ymax and 1.0 are global constants.

int nrows;
int ncols;
int nchan;
int pitch;
int bold;
double xmin, ymin, xmax, ymax;
byte* im;
byte colour[3];
byte gray;

struct Gray
{
    void operator()(int idx)
    {
        im[idx] = gray;
    }
};

struct GrayBold
{
    void operator()(int idx)
    {
        im[idx] = gray;
        im[idx-1] = gray;
        im[idx+1] = gray;
        im[idx-nrows] = gray;
        im[idx+nrows] = gray;
    }
};

struct GrayBold2
{
    void operator()(int idx)
    {
        im[idx] = gray;
        im[idx-1] = gray;
        im[idx+1] = gray;
        im[idx-nrows] = gray;
        im[idx+nrows] = gray;
        im[idx-2] = gray;
        im[idx+2] = gray;
        im[idx-nrows*2] = gray;
        im[idx+nrows*2] = gray;
        im[idx-1-nrows] = gray;
        im[idx+1-nrows] = gray;
        im[idx-1+nrows] = gray;
        im[idx+1+nrows] = gray;
    }
};

struct RGB
{
    void operator()(int idx)
    {
        im[idx] = colour[0];
        im[idx + pitch] = colour[1];
        im[idx + pitch * 2] = colour[2];
    }
};

struct RGBBold
{
    void operator()(int idx)
    {
        im[idx] = colour[0];
        im[idx-1] = colour[0];
        im[idx+1] = colour[0];
        im[idx-nrows] = colour[0];
        im[idx+nrows] = colour[0];
        im[idx + pitch] = colour[1];
        im[idx-1 + pitch] = colour[1];
        im[idx+1 + pitch] = colour[1];
        im[idx-nrows + pitch] = colour[1];
        im[idx+nrows + pitch] = colour[1];
        im[idx + pitch * 2] = colour[2];
        im[idx-1 + pitch * 2] = colour[2];
        im[idx+1 + pitch * 2] = colour[2];
        im[idx-nrows + pitch * 2] = colour[2];
        im[idx+nrows + pitch * 2] = colour[2];
    }
};

template <typename P>
        void bresenham_draw(int y0, int x0, int y1, int x1)
{
    int dx =  abs(x1-x0), sx = x0<x1 ? 1 : -1;
    int dy = -abs(y1-y0), sy = y0<y1 ? 1 : -1;
    int err = dx+dy, e2;                                   /* error value e_xy */
    P putpixel;
    for (;;) {                                                          /* loop */
        int idx = x0 * nrows + y0;
        putpixel(idx);
        e2 = 2*err;
        if (e2 >= dy) {                                         /* e_xy+e_x > 0 */
            if (x0 == x1) break;
            err += dy; x0 += sx;
        }
        if (e2 <= dx) {                                         /* e_xy+e_y < 0 */
            if (y0 == y1) break;
            err += dx; y0 += sy;
        }
    }
}

void bresenham(int y0, int x0, int y1, int x1)
{
    if (bold == 1)
    {
        if (1 == nchan)
            bresenham_draw<GrayBold>(y0, x0, y1, x1);
        else
            bresenham_draw<RGBBold>(y0, x0, y1, x1);
    }
    else
    {
        if (bold == 2)
        {
                    if (1 == nchan)
            bresenham_draw<GrayBold2>(y0, x0, y1, x1);
//         else
//             bresenham_draw<RGBBold2>(y0, x0, y1, x1);
        }
        else
        {
            if (1 == nchan)
                bresenham_draw<Gray>(y0, x0, y1, x1);
            else
                bresenham_draw<RGB>(y0, x0, y1, x1);
        }
    }
}

int ComputeOutCode(double x, double y)
{
    int code;
    
    code = INSIDE;          // initialised as being inside of clip window
    
    if (x < xmin)           // to the left of clip window
        code |= LEFT;
    else if (x > xmax)      // to the right of clip window
        code |= RIGHT;
    if (y < ymin)           // below the clip window
        code |= BOTTOM;
    else if (y > ymax)      // above the clip window
        code |= TOP;
    
    return code;
}

// Cohen–Sutherland clipping algorithm clips a line from
// P0 = (x0, y0) to P1 = (x1, y1) against a rectangle with
// diagonal from (1.0, 1.0) to (xmax, ymax).
void CohenSutherlandLineClipAndDraw(double x0, double y0, double x1, double y1)
{
    // compute outcodes for P0, P1, and whatever point lies outside the clip rectangle
    int outcode0 = ComputeOutCode(x0, y0);
    int outcode1 = ComputeOutCode(x1, y1);
    bool accept = false;
    
    while (true) {
        if (!(outcode0 | outcode1)) { // Bitwise OR is 0. Trivially accept and get out of loop
            accept = true;
            break;
        } else if (outcode0 & outcode1) { // Bitwise AND is not 0. Trivially reject and get out of loop
            break;
        } else {
            // failed both tests, so calculate the line segment to clip
            // from an outside point to an intersection with clip edge
            double x, y;
            
            // At least one endpoint is outside the clip rectangle; pick it.
            int outcodeOut = outcode0 ? outcode0 : outcode1;
            
            // Now find the intersection point;
            // use formulas y = y0 + slope * (x - x0), x = x0 + (1 / slope) * (y - y0)
            if (outcodeOut & TOP) {           // point is above the clip rectangle
                x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0);
                y = ymax;
            } else if (outcodeOut & BOTTOM) { // point is below the clip rectangle
                x = x0 + (x1 - x0) * (xmin - y0) / (y1 - y0);
                y = ymin;
            } else if (outcodeOut & RIGHT) {  // point is to the right of clip rectangle
                y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0);
                x = xmax;
            } else if (outcodeOut & LEFT) {   // point is to the left of clip rectangle
                y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0);
                x = xmin;
            }
            
            // Now we move outside point to intersection point to clip
            // and get ready for next pass.
            if (outcodeOut == outcode0) {
                x0 = x;
                y0 = y;
                outcode0 = ComputeOutCode(x0, y0);
            } else {
                x1 = x;
                y1 = y;
                outcode1 = ComputeOutCode(x1, y1);
            }
        }
    }
    if (accept) {
        bresenham((int)y0 - 1, (int)x0 - 1, (int)y1 - 1, (int)x1 - 1);
    }
}








void mexFunction(int nlhs, mxArray *plhs[], int nrhs,
        const mxArray *prhs[])
{
    if (nrhs != 5)
    {
        mexErrMsgTxt("Expected five arguments.\n");
    }
//     double rs = mxGetScalar(prhs[1]);
//     double cs = mxGetScalar(prhs[2]);
//     double re = mxGetScalar(prhs[3]);
//     double ce = mxGetScalar(prhs[4]);
    
    mxArray const *im_ = prhs[0];
    const mwSize* dims = mxGetDimensions(im_);
    mwSize ndims = mxGetNumberOfDimensions(im_);
    if (ndims > 2)
    {
        nchan = dims[2];
        if (3 != nchan)
            mexErrMsgTxt("The image can be either grayscale or RGB.\n");
    }
    else
        nchan = 1;
    
    mxClassID category = mxGetClassID(im_);
    
    
    if (mxUINT8_CLASS != category) {
        mexErrMsgTxt("Expected an uint8 image.\n");
    }
    
    im = (byte*)mxGetData(im_);
    nrows = dims[0];
    ncols = dims[1];
    pitch = nrows * ncols;
    
    bold = (int)mxGetScalar(prhs[4]);
    if (1 == bold)
    {
        xmin = 2.0;
        xmax = (double)ncols - 1;
        ymin = 2.0;
        ymax = (double)nrows - 1;
    }
    else
    {
        if (2 == bold)
        {
            xmin = 3.0;
            xmax = (double)ncols - 2;
            ymin = 3.0;
            ymax = (double)nrows - 2;
        }
        else
        {
            xmin = 1.0;
            xmax = (double)ncols;
            ymin = 1.0;
            ymax = (double)nrows;
        }
    }
    
    
    mxArray const *start_ = prhs[1];
    double* start = (double*)mxGetData(start_);
    mxArray const *end_ = prhs[2];
    double* end = (double*)mxGetData(end_);
    
    
    mxArray const *col_ = prhs[3];
    double* col = (double*)mxGetData(col_);
    if (mxGetNumberOfElements(col_) != nchan)
        mexErrMsgTxt("Wrong number of colour components.\n");
    if (mxGetN(start_) != mxGetN(end_))
        mexErrMsgTxt("Number of starts must equal the number of ends.\n");
    if ((mxGetM(start_) != 2) || (mxGetM(end_) != 2))
        mexErrMsgTxt("Starts and ends must be 2-by-N.\n");
    
    if (3 == nchan)
    {
        colour[0] = (byte)col[0];
        colour[1] = (byte)col[1];
        colour[2] = (byte)col[2];
    }
    else
    {
        gray = (byte)col[0];
    }
    int nlines = mxGetN(start_);
    for (int i = 0; i < nlines; ++i)
    {
//         CohenSutherlandLineClipAndDraw(start[1], *start, end[1], *end);
        double sx = start[0];
        double sy = start[1];
        double ex = end[0];
        double ey = end[1];
        if (isnan(sx) || isnan(sy) || isnan(ex) || isnan(ey))
            continue;
        CohenSutherlandLineClipAndDraw(sx, sy, ex, ey);
        start += 2;
        end += 2;
    }
}
