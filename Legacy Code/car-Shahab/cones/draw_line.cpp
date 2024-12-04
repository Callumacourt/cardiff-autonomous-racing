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
// int bold;
double alpha;
double xmin, ymin, xmax, ymax;
byte* im;
byte colour[3];
byte gray;

inline double square(double x)
{
    return x * x;
}

inline void lerp(const byte* a, const byte* b, double br, byte* result)
{
//     if (br > 1.0)
//     {
//         br = 1.0;
//     }

            br = 1.0 - square(1.0 - br);
            br = br * alpha;
    result[0] = (1 - br) * (double)a[0] + br * (double)b[0];
    result[1] = (1 - br) * (double)a[1] + br * (double)b[1];
    result[2] = (1 - br) * (double)a[2] + br * (double)b[2];
}

inline void put_pixel_clip(int x, int y, const byte* col)
{
//     if ((x < 0) || (x >= ncols) || (y < 0) || (y >= nrows))
//         return;
    im[x * nrows + y] = col[0];
    im[x * nrows + y + pitch] = col[1];
    im[x * nrows + y + pitch * 2] = col[2];
}

inline void get_pixel_clip(int x, int y, byte* col)
{
//     if ((x < 0) || (x >= ncols) || (y < 0) || (y >= nrows))
//     {
//         col[0] = 0;
//         col[1] = 0;
//         col[2] = 0;
//         return;
//     }
    col[0] = im[x * nrows + y];
    col[1] = im[x * nrows + y + pitch];
    col[2] = im[x * nrows + y + pitch * 2];
}


inline void plot_(int x, int y, double br)
{
    byte before[3];
    get_pixel_clip(x, y, before);
    byte oc[3];
    lerp(before, colour, br, oc);
    put_pixel_clip(x, y, oc);
}

// #define plot_(X,Y,D) do { byte f_[3];			\
// f_[0] = r; f_[1] = g; f_[2] = b;			\
//         _dla_plot(img, (X), (Y), &f_, (D)) ; }while(0)
// inline void plot_(int x, int y, double br)
// {
//     _dla_plot(x, y, colour, br);
// }


#define ipart_(X) ((int)(X))
#define round_(X) ((int)(((double)(X))+0.5))
#define fpart_(X) (((double)(X))-(double)ipart_(X))
#define rfpart_(X) (1.0-fpart_(X))

#define swap_(a, b) do{ __typeof__(a) tmp;  tmp = a; a = b; b = tmp; }while(0)
void draw_line_antialias(
        unsigned int x1, unsigned int y1,
        unsigned int x2, unsigned int y2)
{
    double dx = (double)x2 - (double)x1;
    double dy = (double)y2 - (double)y1;
    if ( fabs(dx) > fabs(dy) ) {
        if ( x2 < x1 ) {
            swap_(x1, x2);
            swap_(y1, y2);
        }
        double gradient = dy / dx;
        double xend = round_(x1);
        double yend = y1 + gradient*(xend - x1);
        double xgap = rfpart_(x1 + 0.5);
        int xpxl1 = xend;
        int ypxl1 = ipart_(yend);
        plot_(xpxl1, ypxl1, rfpart_(yend)*xgap);
        plot_(xpxl1, ypxl1+1, fpart_(yend)*xgap);
        double intery = yend + gradient;
        
        xend = round_(x2);
        yend = y2 + gradient*(xend - x2);
        xgap = fpart_(x2+0.5);
        int xpxl2 = xend;
        int ypxl2 = ipart_(yend);
        plot_(xpxl2, ypxl2, rfpart_(yend) * xgap);
        plot_(xpxl2, ypxl2 + 1, fpart_(yend) * xgap);
        
        int x;
        for(x=xpxl1+1; x <= (xpxl2-1); x++) {
            plot_(x, ipart_(intery), rfpart_(intery));
            plot_(x, ipart_(intery) + 1, fpart_(intery));
            intery += gradient;
        }
    } else {
        if ( y2 < y1 ) {
            swap_(x1, x2);
            swap_(y1, y2);
        }
        double gradient = dx / dy;
        double yend = round_(y1);
        double xend = x1 + gradient*(yend - y1);
        double ygap = rfpart_(y1 + 0.5);
        int ypxl1 = yend;
        int xpxl1 = ipart_(xend);
        plot_(xpxl1, ypxl1, rfpart_(xend)*ygap);
        plot_(xpxl1, ypxl1+1, fpart_(xend)*ygap);
        double interx = xend + gradient;
        
        yend = round_(y2);
        xend = x2 + gradient*(yend - y2);
        ygap = fpart_(y2+0.5);
        int ypxl2 = yend;
        int xpxl2 = ipart_(xend);
        plot_(xpxl2, ypxl2, rfpart_(xend) * ygap);
        plot_(xpxl2, ypxl2 + 1, fpart_(xend) * ygap);
        
        int y;
        for(y=ypxl1+1; y <= (ypxl2-1); y++) {
            plot_(ipart_(interx), y, rfpart_(interx));
            plot_(ipart_(interx) + 1, y, fpart_(interx));
            interx += gradient;
        }
    }
}
#undef swap_
#undef plot_
#undef ipart_
#undef fpart_
#undef round_
#undef rfpart_

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
//         bresenham((int)y0 - 1, (int)x0 - 1, (int)y1 - 1, (int)x1 - 1);
        draw_line_antialias((int)x0 - 1, (int)y0 - 1, (int)x1 - 1, (int)y1 - 1);
        plot_((int)x0 - 1, (int)y0 - 1, alpha);
        plot_((int)x1 - 1, (int)y1 - 1, alpha);
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
    
    alpha = (double)mxGetScalar(prhs[4]);
//     if (bold)
//     {
//         xmin = 2.0;
//         xmax = (double)ncols - 1;
//         ymin = 2.0;
//         ymax = (double)nrows - 1;
//     }
//     else
//     {
        xmin = 1.0;
        xmax = (double)ncols;
        ymin = 1.0;
        ymax = (double)nrows;
//     }
    
    
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
