#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION

#include <numpy/arrayobject.h>
#include <Python.h>

inline int argmax3(int a, int b, int c)
{
    if ((a >= b) && (a >= c))
	return 0;
    if ((b >= a) && (b >= c))
	return 1;
    return 2;
}

/* inline int fargmax3(float a, float b, float c) */
/* { */
/*     if ((a >= b) && (a >= c)) */
/* 	return 0; */
/*     if ((b >= a) && (b >= c)) */
/* 	return 1; */
/*     return 2; */
/* } */

static PyObject *max_argmax(PyObject *self, PyObject *args)
{
    PyArrayObject *det_ = 0;
    PyArrayObject *lab_ = 0;
    PyArrayObject *soft_ = 0;
    if (!PyArg_ParseTuple(args, "O!O!O!",
                          &PyArray_Type, &det_,
                          &PyArray_Type, &lab_,
                          &PyArray_Type, &soft_))
    {
        return NULL;
    }

    int h = PyArray_SHAPE(det_)[0];
    int w = PyArray_SHAPE(det_)[1];
    int hw = h * w;
    float* det = PyArray_DATA(det_);
    unsigned char* lab = PyArray_DATA(lab_);
    float* soft = PyArray_DATA(soft_);

#pragma omp parallel for schedule(guided)
    /* for (float* det_end = det + 3 * hw; det != det_end; det += 3) */
    for (int i = 0; i < hw; ++i)
    {
	/* float a = *det; */
	/* float b = *(det + 1); */
	/* float c = *(det + 2); */
	float a = det[3 * i];
	float b = det[3 * i + 1];
	float c = det[3 * i + 2];
	if (a >= b)
	{
	    if (a >= c)
	    {
		lab[i] = 0;
		soft[i] = a;
	    }
	    else
	    {
		lab[i] = 2;
		soft[i] = c;
	    }
	}
	else
	    if (b >= c)
	    {
		lab[i] = 1;
		soft[i] = b;
	    }
	    else
	    {
		lab[i] = 2;
		soft[i] = c;
	    }
	/* if ((a >= b) && (a >= c)) */
	/* { */
	/*     lab[i] = 0; */
	/*     soft[i] = a; */
	/* } */
	/* else if ((b >= a) && (b >= c)) */
	/* { */
	/*     lab[i] = 1; */
	/*     soft[i] = b; */
	/* } */
	/* else */
	/* { */
	/*     lab[i] = 2; */
	/*     soft[i] = c; */
	/* } */
    }
    
    Py_INCREF(Py_None);
    return Py_None;
}


static PyObject *analyse_cc(PyObject *self, PyObject *args)
{
    PyArrayObject *cc_labels_ = 0;
    PyArrayObject *lab_       = 0;
    PyArrayObject *soft_      = 0;
    PyArrayObject *cones_     = 0;
    if (!PyArg_ParseTuple(args, "O!O!O!O!",
                          &PyArray_Type, &cc_labels_,
                          &PyArray_Type, &lab_,
                          &PyArray_Type, &soft_,
                          &PyArray_Type, &cones_))
    {
        return NULL;
    }

    int h = PyArray_SHAPE(cc_labels_)[0];
    int w = PyArray_SHAPE(cc_labels_)[1];
    /* int hw = h * w; */

    int n_cc                 = PyArray_SHAPE(cones_)[1];
    float* cones             = PyArray_DATA(cones_);
    float const* soft        = PyArray_DATA(soft_);
    int const* cc_labels     = PyArray_DATA(cc_labels_);
    int const* pos           = cc_labels;
    unsigned char const* lab = PyArray_DATA(lab_);

    /* printf("n_cc = %d\n", n_cc); */

    int* lab_count = calloc(n_cc * 3, sizeof(int));
    /* printf("%p\n", lab_count); */
    /* printf("a\n"); */
    for (int row = 0; row < h; ++row)
    {
	for (int col = 0; col < w; ++col)
	{
	    int l = *pos++;
	    if (l)
	    {
		int label = l - 1;
		/* if (label < 0 || label >= n_cc) */
		/* { */
		/*     printf("label = %d\n", label); */
		/* } */
		float val = soft[w * row + col];
		cones[           label] += (float)col * val; /* TODO: Check if +1.0 is necessary */
		cones[n_cc     + label] += (float)row * val;
		cones[n_cc * 3 + label] += val;
		cones[n_cc * 4 + label] += (val > 0.85); /* TODO: This should be a parameter. */
		/* int idx = label * 3 + lab[w * row + col] - 1; */
		/* if (idx < 0 || idx >= n_cc * 3) */
		/* { */
		/*     printf("idx = %d out of range\n", idx); */
		/* } */
		++lab_count[label * 3 + lab[w * row + col] - 1];
	    }
	}	
    }

    /* printf("b\n"); */
/* Compute the dominant label (mode) */
    for (int i = 0; i < n_cc; ++i)
    {
    	cones[n_cc * 2 + i] = argmax3(lab_count[i * 3 + 0], lab_count[i * 3 + 1], lab_count[i * 3 + 2]);
    }
    /* printf("c\n"); */
/* printf("%d %d\n", h, w); */
    free(lab_count);
    /* printf("d\n"); */
    Py_INCREF(Py_None);
    return Py_None;
}


static PyMethodDef ap_methods[] =
{
    {"analyse_cc",  analyse_cc, METH_VARARGS, "Analyse connected components."},
    {"max_argmax",  max_argmax, METH_VARARGS, "Find max and argmax along the third dimension."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


static struct PyModuleDef moduledef =
{
    PyModuleDef_HEAD_INIT,
    "ap",
    "Fast routines for CAR autopilot. Copyright (c) Kirill Sidorov and Cardiff Racing Driverless, 2020.",
    -1,
    ap_methods,
    NULL, NULL, NULL, NULL
};


PyMODINIT_FUNC PyInit_ap()
{
    import_array();
    return PyModule_Create(&moduledef);
}
