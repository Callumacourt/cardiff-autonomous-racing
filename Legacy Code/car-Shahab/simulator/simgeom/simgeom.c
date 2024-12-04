#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION

#include <numpy/arrayobject.h>
#include <Python.h>
#include <math.h>

#define MAX(a, b) (a > b ? a : b)

inline double tri_area(double x1, double y1, double x2, double y2, double x3, double y3)
{
  return 0.5 * fabs(x1*y2 + x2*y3 + x3*y1 - x2*y1 - x3*y2 - x1*y3);
}

static PyObject *point_in_rect(PyObject *self, PyObject *args)
{
  double x, y, sxtl, sytl, sxtr, sytr, sxbl, sybl, sxbr, sybr, a;
  if (!PyArg_ParseTuple(args, "ddddddddddd",
                        &x, &y, &sxtl, &sytl, &sxtr, &sytr, &sxbl, &sybl, &sxbr, &sybr, &a))
    {
      return NULL;
    }

  double a1 = tri_area(x, y, sxtl, sytl, sxtr, sytr);
  double a2 = tri_area(x, y, sxtr, sytr, sxbr, sybr);
  double a3 = tri_area(x, y, sxbr, sybr, sxbl, sybl);
  double a4 = tri_area(x, y, sxbl, sybl, sxtl, sytl);

  int result =  a1 + a2 + a3 + a4 <= a + 0.0001;

  return Py_BuildValue("i", result);
}

inline void beam_segment(double x0, double y0, double dx, double dy, double ax, double ay, double bx, double by, int *intersects, double *d, double *ix, double *iy)
{
  double dxs = bx - ax;
  double dys = by - ay;
  double denom = dy * dxs - dys * dx;
  *intersects = 0;
  if (fabs(denom) < 0.000001)
    return;
  double t2 = ((ay - y0) * dx + (x0 - ax) * dy) / denom;
  if (t2 < 0.0 || t2 > 1.0)
    return;
  *d = (ax + t2 * dxs - x0) / dx;
  if (*d < 0)
    return;
  *intersects = 1;
  *ix = ax + dxs * t2;
  *iy = ay + dys * t2;
}

void beam_poly(double x0, double y0, double dx, double dy, double const* points, int N, int *found, double *min_d, double *min_ix, double *min_iy)
{
  *min_d = 1e10;
  *found = 0;
  for (int i = 0; i < N; ++i)
    {
      double ax = points[i * 2];
      double ay = points[i * 2 + 1];
      double bx = points[((i + 1) % N) * 2];
      double by = points[((i + 1) % N) * 2 + 1];
      double d, ix, iy;
      int ints;
      beam_segment(x0, y0, dx, dy, ax, ay, bx, by, &ints, &d, &ix, &iy);
      if (ints && (d < *min_d))
        {
          *min_d = d;
          *min_ix = ix;
          *min_iy = iy;
          *found = 1;
        }
    }
}

static PyObject *beam_poly_intersection(PyObject *self, PyObject *args)
{
  PyArrayObject *points_ = 0;
  double x0, y0, dx, dy;
  if (!PyArg_ParseTuple(args, "ddddO!",
                        &x0, &y0, &dx, &dy, &PyArray_Type, &points_))
    {
      return NULL;
    }
  int N = PyArray_SHAPE(points_)[1];
  double const *points = PyArray_DATA(points_);

  int found;
  double min_d, min_ix, min_iy;
  beam_poly(x0, y0, dx, dy, points, N, &found, &min_d, &min_ix, &min_iy);
  return Py_BuildValue("iddd", found, min_d, min_ix, min_iy);
}

static PyObject *any_point_in_rect(PyObject *self, PyObject *args)
{
  PyArrayObject *points_ = 0;
  double sxtl, sytl, sxtr, sytr, sxbl, sybl, sxbr, sybr, a;
  if (!PyArg_ParseTuple(args, "O!ddddddddd",
                        &PyArray_Type, &points_, &sxtl, &sytl, &sxtr, &sytr, &sxbl, &sybl, &sxbr, &sybr, &a))
    {
      return NULL;
    }

  int N = PyArray_SHAPE(points_)[1];
  double const *points = PyArray_DATA(points_);

  for (int i = 0; i < N; ++i)
    {
      double x = points[i * 2];
      double y = points[i * 2 + 1];
      double a1 = tri_area(x, y, sxtl, sytl, sxtr, sytr);
      double a2 = tri_area(x, y, sxtr, sytr, sxbr, sybr);
      double a3 = tri_area(x, y, sxbr, sybr, sxbl, sybl);
      double a4 = tri_area(x, y, sxbl, sybl, sxtl, sytl);
      if (a1 + a2 + a3 + a4 <= a + 0.0001)
        return Py_BuildValue("i", 1);
    }

  return Py_BuildValue("i", 0);
}


#define MAX_DIST 100.0

static PyObject *project_points(PyObject *self, PyObject *args)
{
  PyArrayObject *points_ = 0;
  PyArrayObject *sensors_ = 0;
  double fov, posx, posy, theta;
  if (!PyArg_ParseTuple(args, "O!O!dddd",
                        &PyArray_Type, &points_,
                        &PyArray_Type, &sensors_,
                        &fov, &posx, &posy, &theta))
    {
      return NULL;
    }

  int N = PyArray_SHAPE(points_)[1];
  int resolution = PyArray_SHAPE(sensors_)[1]; /* Number of basis vectors */
  double const *points = PyArray_DATA(points_);
  double *sensors = PyArray_DATA(sensors_);

  double x2 = cos(theta);
  double y2 = sin(theta);

  for (int i = 0; i < resolution; ++i)
    sensors[i] = 0;
  for (int j = 0; j < N; ++j) {
    double x1 = points[j * 2] - posx;
    double y1 = points[j * 2 + 1] - posy;
    double d = sqrt(x1 * x1 + y1 * y1);

    if (d <= MAX_DIST)
      {
        double a = atan2(x1 * y2 - y1 * x2, x1 * x2 + y1 * y2);
        double step = fov / (double)resolution;
        double left = -fov * 0.5;
        for (int i = 0; i < resolution; ++i, left += step)
          {
            if ((a >= left) && (a < left + step))
              {
                double invd = 1.0 - d / MAX_DIST;
                sensors[resolution - 1 - i] = MAX(sensors[resolution - 1 - i], invd);
              }
          }
      }
  }

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *sensors_polar(PyObject *self, PyObject *args)
{
  PyArrayObject *points_ = 0;
  PyArrayObject *sensors_ = 0;
  double fov, posx, posy, theta;
  if (!PyArg_ParseTuple(args, "O!O!dddd",
                        &PyArray_Type, &points_,
                        &PyArray_Type, &sensors_,
                        &fov, &posx, &posy, &theta))
    {
      return NULL;
    }

  int N = PyArray_SHAPE(points_)[1];
  int n_dist = PyArray_SHAPE(sensors_)[0];
  int n_angle = PyArray_SHAPE(sensors_)[1];
  double const *points = PyArray_DATA(points_);
  double *sensors = PyArray_DATA(sensors_);


  double x2 = cos(theta);
  double y2 = sin(theta);

  for (int i = 0; i < n_dist; ++i)
    for (int j = 0; j < n_angle; ++j)
      sensors[i * n_dist + j] = 0;
  
  for (int i = 0; i < N; ++i) {
    double x1 = points[i * 2] - posx;
    double y1 = points[i * 2 + 1] - posy;
    double d = sqrt(x1 * x1 + y1 * y1) / MAX_DIST;
    if (d >= 1.0)
      continue;
    double a = (atan2(x1 * y2 - y1 * x2, x1 * x2 + y1 * y2) / fov) + 0.5;
    if (a < 0.0 || a >= 1.0)
      continue;

    sensors[(int)(d * n_dist) * n_dist + (int)(a * n_angle)] += 1;
  }

  Py_INCREF(Py_None);
  return Py_None;
}



static PyObject *car_bbox(PyObject *self, PyObject *args)
{
  double posx, posy, theta, length, width;
  if (!PyArg_ParseTuple(args, "ddddd",
                        &posx, &posy, &theta, &length, &width))
    {
      return NULL;
    }
  /* return (x * math.cos(theta) - y * math.sin(theta), x * math.sin(theta) + y * math.cos(theta)) */

  double w = 0.5 * width;
  double l = 0.5 * length;
  double st = sin(theta);
  double ct = cos(theta);
  double sxtl = -l * ct + w * st + posx;
  double sytl = -l * st - w * ct + posy;
  double sxtr = +l * ct + w * st + posx;
  double sytr = +l * st - w * ct + posy;
  double sxbl = -l * ct - w * st + posx;
  double sybl = -l * st + w * ct + posy;
  double sxbr = +l * ct - w * st + posx;
  double sybr = +l * st + w * ct + posy;

  /* sxtr, sytr = rotate(+0.5 * self.LENGTH, -0.5 * self.WIDTH, theta) */
  /* sxbl, sybl = rotate(-0.5 * self.LENGTH, +0.5 * self.WIDTH, theta) */
  /* sxbr, sybr = rotate(+0.5 * self.LENGTH, +0.5 * self.WIDTH, theta) */

  /* sxtl += self.posx */
  /* sytl += self.posy */
  /* sxtr += self.posx */
  /* sytr += self.posy */
  /* sxbl += self.posx */
  /* sybl += self.posy */
  /* sxbr += self.posx */
  /* sybr += self.posy */

  return Py_BuildValue("dddddddd", sxtl, sytl, sxtr, sytr, sxbl, sybl, sxbr, sybr);
}

static PyMethodDef simgeom_methods[] =
  {
   {"point_in_rect", point_in_rect, METH_VARARGS, "Check whether a point is in a rectangle."},
   {"any_point_in_rect", any_point_in_rect, METH_VARARGS, "Check whether any point is in a rectangle."},
   {"project_points", project_points, METH_VARARGS, "Project cones onto the sensor plane."},
   {"sensors_polar", sensors_polar, METH_VARARGS, "Get a grid of polar sensor readings."},
   {"car_bbox", car_bbox, METH_VARARGS, "Compute car bounding box."},
   {"beam_poly_intersection", beam_poly_intersection, METH_VARARGS, "Find intersection of a beam with a polygon."},
   {NULL, NULL, 0, NULL}        /* Sentinel */
  };


static struct PyModuleDef moduledef =
  {
   PyModuleDef_HEAD_INIT,
   "simgeom",
   "Geometric functions for the simulator. Copyright (c) Kirill Sidorov and Cardiff Racing Driverless, 2019.",
   -1,
   simgeom_methods,
   NULL, NULL, NULL, NULL
  };


PyMODINIT_FUNC PyInit_simgeom()
{
  import_array();
  return PyModule_Create(&moduledef);
}
