#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION

#include <numpy/arrayobject.h>
#include <Python.h>

#define SQUARE(x) ((x) * (x))

int w, h, d, texw, texh, texd;

typedef unsigned char byte;

float *buf;
byte const *tex;
int bufpitch;
int texpitch;

double top;
double left;
double width;
double height;

#define MIN(a, b) (a < b ? a : b)
#define MAX(a, b) (a > b ? a : b)

// Bilinear sampling, RGB image
void getwnd_rgb_bl()
{
    texpitch = texw * texh;
    bufpitch = h * w;

    byte const *texr = tex;
    byte const *texg = tex + 1;
    byte const *texb = tex + 2;
    double scale_a = (double)(width) / (double)(w);
    double scale_b = (double)(height) / (double)(h);

    if (left >= 0 && top >= 0 && ceil(left + width) <= texw && ceil(top + height) <= texh)
    {
        // Fast case with no checks

#pragma omp parallel for schedule(static)
        for (int col = 0; col < w; ++col)
        {
            double x = left + 0.5 * scale_a - 0.5 + (scale_a * col);
            int ix = (int)x;
            double fx = x - (double)ix;

            float *destr = buf + col * h;
            float *destg = destr + bufpitch;
            float *destb = destg + bufpitch;

            double y = top + 0.5 * scale_b - 0.5;
            for (int row = 0; row < h; ++row)
            {
                int iy = (int)y;
                double fy = y - (double)iy;

                int A = iy * texw * 3;
                int B = A + texw * 3;

                double c1, c2;
                int a = texr[A + ix * 3];
                int b = texr[A + ix * 3 + 3];
                c1 = a + ((int)texr[B + ix * 3] - a) * fy;
                c2 = b + ((int)texr[B + ix * 3 + 3] - b) * fy;
                *destr = (c1 + (c2 - c1) * fx);

                a = texg[A + ix * 3];
                b = texg[A + ix * 3 + 3];
                c1 = a + ((int)texg[B + ix * 3] - a) * fy;
                c2 = b + ((int)texg[B + ix * 3 + 3] - b) * fy;
                *destg = (c1 + (c2 - c1) * fx);

                a = texb[A + ix * 3];
                b = texb[A + ix * 3 + 3];
                c1 = a + ((int)texb[B + ix * 3] - a) * fy;
                c2 = b + ((int)texb[B + ix * 3 + 3] - b) * fy;
                *destb = (c1 + (c2 - c1) * fx);

                ++destr;
                ++destg;
                ++destb;
                y += scale_b;
            }
        }
    }
    else // Slow case with checks
    {
        for (int col = 0; col < w; ++col)
        {
            double x = left + 0.5 * scale_a - 0.5 + (scale_a * col);
            int ix = (int)x;
            double fx = x - (double)ix;

            float *destr = buf + col * h;
            float *destg = destr + bufpitch;
            float *destb = destg + bufpitch;

            for (int row = 0; row < h; ++row) {
                double y = top + 0.5 * scale_b - 0.5 + (scale_b * row);
                int iy = (int)y;
                double fy = y - (double)iy;

                int A = MAX(0, MIN(iy, texh-1)) * texw * 3;
                int B = MAX(0, MIN(iy+1, texh-1)) * texw * 3;

                int oful = A + MAX(0, MIN(ix, texw-1) * 3);
                int ofur = A + MAX(0, MIN(ix+1, texw-1) * 3);
                int ofdl = B + MAX(0, MIN(ix, texw-1)) * 3;
                int ofdr = B + MAX(0, MIN(ix+1, texw-1) * 3);

                double c1, c2;
                c1 = texr[oful] + ((int)texr[ofdl] - (int)texr[oful]) * fy;
                c2 = texr[ofur] + ((int)texr[ofdr] - (int)texr[ofur]) * fy;
                *destr = (c1 + (c2 - c1) * fx);

                c1 = texg[oful] + ((int)texg[ofdl] - (int)texg[oful]) * fy;
                c2 = texg[ofur] + ((int)texg[ofdr] - (int)texg[ofur]) * fy;
                *destg = (c1 + (c2 - c1) * fx);

                c1 = texb[oful] + ((int)texb[ofdl] - (int)texb[oful]) * fy;
                c2 = texb[ofur] + ((int)texb[ofdr] - (int)texb[ofur]) * fy;
                *destb = (c1 + (c2 - c1) * fx);

                ++destr;
                ++destg;
                ++destb;
            }
        }
    }
}


// Nearest neighbour sampling, RGB image
void getwnd_rgb_nn()
{
    texpitch = texw * texh;
    bufpitch = h * w;

    byte const *texr = tex;
    byte const *texg = tex + 1;
    byte const *texb = tex + 2;
    double scale_a = (double)(width) / (double)(w);
    double scale_b = (double)(height) / (double)(h);

    if (left >= 0 && top >= 0 && ceil(left + width) <= texw && ceil(top + height) <= texh)
    {
        // Fast case with no checks
#pragma omp parallel for schedule(static)
        for (int col = 0; col < w; ++col) {
            double x = left + 0.5 * scale_a + (scale_a * col);
            int ix = (int)x;

            float *destr = buf + col * h;
            float *destg = destr + bufpitch;
            float *destb = destg + bufpitch;

            byte const *tr = texr + ix * 3;
            byte const *tg = texg + ix * 3;
            byte const *tb = texb + ix * 3;
            double y = top + 0.5 * scale_b;
#pragma omp simd
            for (int row = 0; row < h; ++row) {
                int iy = (int)y;
                int a = (iy * texw) * 3;
                *destr++ = tr[a];
                *destg++ = tg[a];
                *destb++ = tb[a];
                y += scale_b;
            }
        }
    }
    else // Slow case with checks
    {
        for (int col = 0; col < w; ++col)
        {
            double x = left + 0.5 * scale_a + (scale_a * col);
            int ix = (int)x;

            float *destr = buf + col * h;
            float *destg = destr + bufpitch;
            float *destb = destg + bufpitch;

            int t = MAX(0, MIN(ix, texw-1) * 3);
            for (int row = 0; row < h; ++row)
            {
                double y = top + 0.5 * scale_b + (scale_b * row);
                int iy = (int)y;

                int a = MAX(0, MIN(iy, texh-1)) * texw * 3 + t;
                *destr++ = texr[a];
                *destg++ = texg[a];
                *destb++ = texb[a];
            }
        }
    }
}


void getwnd_gray_bl()
{
}


void getwnd_gray_nn()
{
}


static PyObject *amsvm_getwnd_bl(PyObject *self, PyObject *args)
{
    PyArrayObject *buf_ = 0;
    PyArrayObject *tex_ = 0;
    if (!PyArg_ParseTuple(args, "O!O!dddd",
                          &PyArray_Type, &buf_,
                          &PyArray_Type, &tex_,
                          &left, &top, &width, &height))
    {
        return NULL;
    }

    texh = PyArray_SHAPE(tex_)[0];
    texw = PyArray_SHAPE(tex_)[1];
    texd = PyArray_SHAPE(tex_)[2];
    h = PyArray_SHAPE(buf_)[0];
    w = PyArray_SHAPE(buf_)[1];

    tex = PyArray_DATA(tex_);
    buf = PyArray_DATA(buf_);

    if (texd == 3)
        getwnd_rgb_bl();
    else
        getwnd_gray_bl();

    Py_INCREF(Py_None);
    return Py_None;
}


static PyObject *amsvm_getwnd_nn(PyObject *self, PyObject *args)
{
    PyArrayObject *buf_ = 0;
    PyArrayObject *tex_ = 0;
    if (!PyArg_ParseTuple(args, "O!O!dddd",
                          &PyArray_Type, &buf_,
                          &PyArray_Type, &tex_,
                          &left, &top, &width, &height))
    {
        return NULL;
    }

    texh = PyArray_SHAPE(tex_)[0];
    texw = PyArray_SHAPE(tex_)[1];
    texd = PyArray_SHAPE(tex_)[2];
    h = PyArray_SHAPE(buf_)[0];
    w = PyArray_SHAPE(buf_)[1];

    tex = PyArray_DATA(tex_);
    buf = PyArray_DATA(buf_);

    if (texd == 3)
        getwnd_rgb_nn();
    else
        getwnd_gray_nn();

    Py_INCREF(Py_None);
    return Py_None;
}


inline float predict(int Nv, int Nb, float const *x, float const *vectors, float const *alphas, float const b, float const scale)
{
    float res = 0.0;
#pragma omp parallel for schedule(guided) reduction (+:res)
    for (int j = 0; j < Nv; ++j)
    {
        float const *v = vectors + j * Nb;
        float sum = 0.0;
#pragma omp simd reduction(+:sum)
        for (int k = 0; k < Nb; ++k)
        {
            sum += SQUARE(x[k] - v[k]);
        }
        res += alphas[j] * exp(-sum * scale);
    }
    return res + b;
}


inline void project(float *proj, float const* B, float const *X, int Nb, int dim)
{
#pragma omp parallel for schedule(guided)
    for (int j = 0; j < Nb; ++j)
    {
        float const *b = B + j * dim;
        float sum = 0.0;
#pragma omp simd reduction(+:sum)
        for (int k = 0; k < dim; ++k)
        {
            sum += X[k] * b[k];
        }
        proj[j] = sum;
    }
}


static PyObject *amsvm_am_project_svm(PyObject *self, PyObject *args)
{
    PyArrayObject *X_ = 0;
    PyArrayObject *B_ = 0;
    PyArrayObject *sd_min_ = 0;
    PyArrayObject *sd_max_ = 0;
    PyArrayObject *vectors_ = 0;
    PyArrayObject *alphas_ = 0;
    double bias, scale;
    if (!PyArg_ParseTuple(args, "O!O!O!O!O!O!dd",
                          &PyArray_Type, &X_,
                          &PyArray_Type, &B_,
                          &PyArray_Type, &sd_min_,
                          &PyArray_Type, &sd_max_,
                          &PyArray_Type, &vectors_,
                          &PyArray_Type, &alphas_,
                          &bias, &scale))
    {
        return NULL;
    }

    int Xh = PyArray_SHAPE(X_)[0];
    int Xw = PyArray_SHAPE(X_)[1];
    int Xd = PyArray_SHAPE(X_)[2];

    int dim = Xw * Xh * Xd; /* Dimensionality of data */
    int Nb = PyArray_SHAPE(B_)[1]; /* Number of basis vectors */
    int Nv = PyArray_SHAPE(vectors_)[1]; /* Number of support vectors (and alphas) */

    /* AM parameters */
    float const *X = PyArray_DATA(X_);
    float const *B = PyArray_DATA(B_);
    float const *sd_min = PyArray_DATA(sd_min_);
    float const *sd_max = PyArray_DATA(sd_max_);

    /* SVM parameters */
    float const *vectors = PyArray_DATA(vectors_);
    float const *alphas = PyArray_DATA(alphas_);

    float *proj = malloc(Nb * sizeof(float));
    project(proj, B, X, Nb, dim);

    /* for (int i = 0; i < Nb; ++i) { */
    /*   if ((proj[i] < sd_min[i]) || (proj[i] > sd_max[i])) { */
    /*     free(proj); */
    /*     return Py_BuildValue("f", -10.0); */
    /*   } */
    /* } */

    float pred = predict(Nv, Nb, proj, vectors, alphas, bias, scale);
    free(proj);
    return Py_BuildValue("f", pred);
}


static PyObject *amsvm_am_project_svm2(PyObject *self, PyObject *args)
{
    PyArrayObject *X_ = 0;
    PyArrayObject *B_ = 0;
    PyArrayObject *sd_min_ = 0;
    PyArrayObject *sd_max_ = 0;
    PyArrayObject *vectors1_ = 0;
    PyArrayObject *alphas1_ = 0;
    double bias1, scale1;
    PyArrayObject *vectors2_ = 0;
    PyArrayObject *alphas2_ = 0;
    double bias2, scale2;
    if (!PyArg_ParseTuple(args, "O!O!O!O!O!O!ddO!O!dd",
                          &PyArray_Type, &X_,
                          &PyArray_Type, &B_,
                          &PyArray_Type, &sd_min_,
                          &PyArray_Type, &sd_max_,
                          &PyArray_Type, &vectors1_,
                          &PyArray_Type, &alphas1_,
                          &bias1, &scale1,
                          &PyArray_Type, &vectors2_,
                          &PyArray_Type, &alphas2_,
                          &bias2, &scale2))
    {
        return NULL;
    }

    int Xh = PyArray_SHAPE(X_)[0];
    int Xw = PyArray_SHAPE(X_)[1];
    int Xd = PyArray_SHAPE(X_)[2];

    int dim = Xw * Xh * Xd; /* Dimensionality of data */
    int Nb = PyArray_SHAPE(B_)[1]; /* Number of basis vectors */
    int Nv1 = PyArray_SHAPE(vectors1_)[1]; /* Number of support vectors (and alphas) */
    int Nv2 = PyArray_SHAPE(vectors2_)[1]; /* Number of support vectors (and alphas) */

    /* AM parameters */
    float const *X = PyArray_DATA(X_);
    float const *B = PyArray_DATA(B_);
    float const *sd_min = PyArray_DATA(sd_min_);
    float const *sd_max = PyArray_DATA(sd_max_);

    /* SVM parameters */
    float const *vectors1 = PyArray_DATA(vectors1_);
    float const *alphas1 = PyArray_DATA(alphas1_);
    float const *vectors2 = PyArray_DATA(vectors2_);
    float const *alphas2 = PyArray_DATA(alphas2_);

    float *proj = malloc(Nb * sizeof(float));
    project(proj, B, X, Nb, dim);

    /* for (int i = 0; i < Nb; ++i) { */
    /*   if ((proj[i] < sd_min[i]) || (proj[i] > sd_max[i])) { */
    /*     free(proj); */
    /*     return Py_BuildValue("f", -10.0); */
    /*   } */
    /* } */

    float pred1 = predict(Nv1, Nb, proj, vectors1, alphas1, bias1, scale1);
    float pred2 = predict(Nv2, Nb, proj, vectors2, alphas2, bias2, scale2);
    free(proj);
    return Py_BuildValue("ff", pred1, pred2);
}


static PyMethodDef amsvm_methods[] =
{
    {"getwndbl",  amsvm_getwnd_bl, METH_VARARGS, "Sample a window into a buffer with bilinear sampling."},
    {"getwndnn",  amsvm_getwnd_nn, METH_VARARGS, "Sample a window into a buffer with nearest neighbour sampling."},
    {"am_project_svm",  amsvm_am_project_svm, METH_VARARGS, "Project buffer onto AM and evaluate with SVM."},
    {"am_project_svm2",  amsvm_am_project_svm2, METH_VARARGS, "Project buffer onto AM and evaluate with two SVMs."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


static struct PyModuleDef moduledef =
{
    PyModuleDef_HEAD_INIT,
    "amsvm",
    "Classifying images using eigenspace appearanece models and SVM. Copyright (c) Kirill Sidorov and Cardiff Racing Driverless, 2019.",
    -1,
    amsvm_methods,
    NULL, NULL, NULL, NULL
};


PyMODINIT_FUNC PyInit_amsvm()
{
    import_array();
    return PyModule_Create(&moduledef);
}
