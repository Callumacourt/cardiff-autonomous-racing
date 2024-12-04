#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION

#include <numpy/arrayobject.h>
#include <Python.h>
#include <math.h>

/* #define MAX(a, b) (a > b ? a : b) */

inline double pi2pi(const double angle)
{
  double a = fmod((angle + M_PI), (2.0 * M_PI)) - M_PI;
  if (a < -M_PI)
    a += 2.0 * M_PI;
  if (a > M_PI)
    a -= 2.0 * M_PI;
  return a;
}


static PyObject *compute_jacobians(PyObject *self, PyObject *args)
{
  PyArrayObject *Pf_ = 0;
  PyArrayObject *Q_cov_ = 0;
  double xfx, xfy, px, py, pyaw;

  /* Output */
  PyArrayObject *zp_ = 0;
  PyArrayObject *Hv_ = 0;
  PyArrayObject *Hf_ = 0;
  PyArrayObject *Sf_ = 0;

  if (!PyArg_ParseTuple(args, "dddddO!O!O!O!O!O!",
                        &xfx, &xfy, &px, &py, &pyaw,
                        &PyArray_Type, &Pf_, &PyArray_Type, &Q_cov_,
                        &PyArray_Type, &zp_, &PyArray_Type, &Hv_,
                        &PyArray_Type, &Hf_, &PyArray_Type, &Sf_))
    {
      return NULL;
    }
  double const *Pf = PyArray_DATA(Pf_);
  double const *Q_cov = PyArray_DATA(Q_cov_);

  double *zp = PyArray_DATA(zp_);
  double *Hv = PyArray_DATA(Hv_);
  double *Hf = PyArray_DATA(Hf_);
  double *Sf = PyArray_DATA(Sf_);


  double dx = xfx - px;
  double dy = xfy - py;
  double d2 = dx * dx + dy * dy;
  double dd = sqrt(d2);
  zp[0] = dd;
  zp[1] = pi2pi(atan2(dy, dx) - pyaw);
  Hv[0] = -dx / dd; Hv[1] = -dy / dd; Hv[2] = 0.0;
  Hv[3] = dy / d2; Hv[4] = -dx / d2; Hv[5] = -1.0;
  Hf[0] = dx / dd; Hf[1] = dy / dd;
  Hf[2] = -dy / d2; Hf[3] = dx / d2;
  double a = Hf[1] * Pf[2] + Hf[0] * Pf[0];
  double b = Hf[1] * Pf[3] + Hf[0] * Pf[1];
  double c = Hf[3] * Pf[2] + Hf[2] * Pf[0];
  double d = Hf[3] * Pf[3] + Hf[2] * Pf[1];

  Sf[0] = Hf[1] * b + Hf[0] * a + Q_cov[0];
  Sf[1] = Hf[3] * b + Hf[2] * a + Q_cov[1];
  Sf[2] = Hf[1] * d + Hf[0] * c + Q_cov[2];
  Sf[3] = Hf[3] * d + Hf[2] * c + Q_cov[3];

  /* # Sf = Hf @ Pf @ Hf.T + Q_cov */

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *update_kf_with_cholesky(PyObject *self, PyObject *args)
{
  PyArrayObject *xf_ = 0;
  PyArrayObject *Pf_ = 0;
  PyArrayObject *v_ = 0;
  PyArrayObject *Q_cov_ = 0;
  PyArrayObject *Hf_ = 0;

  /* Output */
  PyArrayObject *x_ = 0;
  PyArrayObject *P_ = 0;

  if (!PyArg_ParseTuple(args, "O!O!O!O!O!O!O!",
                        &PyArray_Type, &xf_, &PyArray_Type, &Pf_,
                        &PyArray_Type, &v_, &PyArray_Type, &Q_cov_,
                        &PyArray_Type, &Hf_, &PyArray_Type, &x_,
                        &PyArray_Type, &P_))
    {
      return NULL;
    }
  double const *xf = PyArray_DATA(xf_);
  double const *Pf = PyArray_DATA(Pf_);
  double const *v = PyArray_DATA(v_);
  double const *Q = PyArray_DATA(Q_cov_);
  double const *Hf = PyArray_DATA(Hf_);

  double *x = PyArray_DATA(x_);
  double *P = PyArray_DATA(P_);

  /* PHt = Pf @ Hf.T */
  double PHt0 = Hf[1]*Pf[1] + Hf[0]*Pf[0];
  double PHt1 = Hf[3]*Pf[1] + Hf[2]*Pf[0];
  double PHt2 = Hf[1]*Pf[3] + Hf[0]*Pf[2];
  double PHt3 = Hf[3]*Pf[3] + Hf[2]*Pf[2];

  /*   S = Hf @ PHt + Q_cov */
  double S0 = Q[0]+Hf[1]*PHt2+Hf[0]*PHt0;
  double S1 = Q[1]+Hf[1]*PHt3+Hf[0]*PHt1;
  double S2 = Q[2]+Hf[3]*PHt2+Hf[2]*PHt0;
  double S3 = Q[3]+Hf[3]*PHt3+Hf[2]*PHt1;

  /*   S = (S + S.T) * 0.5 */
  S1 = 0.5 * (S1 + S2);
  S2 = S1;

  /* SChol = np.linalg.cholesky(S).T */
  double C0 = sqrt(S0);
  double C1 = S1 / C0;
  double C3 = sqrt(S3 - C1 * C1);
  double C2 = (S1 - C0 * C1) / C3;
  /* printf("%.3f %.3f\n%.3f %.3f\n", C0, C1, C2, C3); */

  /* SCholInv = np.linalg.inv(SChol) */
  double inv_det = 1.0 / (C0 * C3 - C1 * C2);
  double Ci0 = C3 * inv_det;
  double Ci1 = -C1 * inv_det;
  double Ci2 = -C2 * inv_det;
  double Ci3 = C0 * inv_det;
  /* printf("%.3f %.3f\n%.3f %.3f\n", Ci0, Ci1, Ci2, Ci3); */

  /* W1 = PHt @ SCholInv */
  double W10 = Ci2*PHt1+Ci0*PHt0;
  double W11 = Ci3*PHt1+Ci1*PHt0;
  double W12 = Ci2*PHt3+Ci0*PHt2;
  double W13 = Ci3*PHt3+Ci1*PHt2;
  /* printf("%.3f %.3f\n%.3f %.3f\n", W10, W11, W12, W13); */

  /* W = W1 @ SCholInv.T */
  double W0 = Ci1*W11+Ci0*W10;
  double W1 = Ci3*W11+Ci2*W10;
  double W2 = Ci1*W13+Ci0*W12;
  double W3 = Ci3*W13+Ci2*W12;
  /* printf("%.3f %.3f\n%.3f %.3f\n", W0, W1, W2, W3); */

  /*   x = xf + W @ v */
  x[0] = xf[0] + v[0] * W0 + v[1] * W1;
  x[1] = xf[1] + v[0] * W2 + v[1] * W3;
  /* printf("%.3f %.3f\n", x[0], x[1]); */


  /*   P = Pf - W1 @ W1.T */
  P[0] = Pf[0] - W11*W11 - W10*W10;
  double t = W11*W13+W10*W12;
  P[1] = Pf[1] - t;
  P[2] = Pf[2] - t;
  P[3] = Pf[3] - W13*W13 - W12*W12;
  /* printf("%.3f %.3f\n%.3f %.3f\n", P[0], P[1], P[2], P[3]); */

  Py_INCREF(Py_None);
  return Py_None;
}



static PyObject *proposal_sampling(PyObject *self, PyObject *args)
{
  PyArrayObject *Sf_ = 0;
  PyArrayObject *Hv_ = 0;
  PyArrayObject *dz_ = 0;

  /* Output */
  PyArrayObject *x_ = 0;
  PyArrayObject *P_ = 0;

  if (!PyArg_ParseTuple(args, "O!O!O!O!O!",
                        &PyArray_Type, &Sf_, &PyArray_Type, &Hv_,
                        &PyArray_Type, &dz_, &PyArray_Type, &x_,
                        &PyArray_Type, &P_))
    {
      return NULL;
    }
  double const *Sf = PyArray_DATA(Sf_);
  double const *Hv = PyArray_DATA(Hv_);
  double const *dz = PyArray_DATA(dz_);

  double *x = PyArray_DATA(x_);
  double *P = PyArray_DATA(P_);

  /* Pi = np.linalg.inv(P) */
  double A = P[4] * P[8] - P[5] * P[7];
  double B = -P[3] * P[8] + P[5] * P[6];
  double C = P[3] * P[7] - P[4] * P[6];
  double inv_det = 1.0 / (P[0] * A + P[1] * B + P[2] * C);

  double Pi0 = inv_det * A;
  double Pi3 = inv_det * B;
  double Pi6 = inv_det * C;

  double Pi1 = (-P[1] * P[8] + P[2] * P[7]) * inv_det; // D
  double Pi4 = (P[0] * P[8] - P[2] * P[6]) * inv_det; // E
  double Pi7 = (-P[0] * P[7] + P[1] * P[6]) * inv_det; // F

  double Pi2 = (P[1] * P[5] - P[2] * P[4]) * inv_det; // G
  double Pi5 = (-P[0] * P[5] + P[2] * P[3]) * inv_det; // H
  double Pi8 = (P[0] * P[4] - P[1] * P[3]) * inv_det; // I

  /* printf("%.3f %.3f %.3f\n%.3f %.3f %.3f\n%.3f %.3f %.3f\n", Pi0, Pi1, Pi2, Pi3, Pi4, Pi5, Pi6, Pi7, Pi8); */

  /* Sfi = np.linalg.inv(Sf) */
  inv_det = 1.0 / (Sf[0] * Sf[3] - Sf[1] * Sf[2]);
  double Sfi0 = Sf[3] * inv_det;
  double Sfi1 = -Sf[1] * inv_det;
  double Sfi2 = -Sf[2] * inv_det;
  double Sfi3 = Sf[0] * inv_det;

  /* printf("%.3f %.3f\n%.3f %.3f\n", Sfi0, Sfi1, Sfi2, Sfi3); */

  /*   particle.P = np.linalg.inv(Hv.T @ Sfi @ Hv + Pi)  # proposal covariance */
  double a = Hv[3]*Sfi2+Hv[0]*Sfi0;
  double b = Hv[3]*Sfi3+Hv[0]*Sfi1;
  double c = Hv[4]*Sfi2+Hv[1]*Sfi0;
  double d = Hv[4]*Sfi3+Hv[1]*Sfi1;
  double e = Hv[5]*Sfi2+Hv[2]*Sfi0;
  double f = Hv[5]*Sfi3+Hv[2]*Sfi1;

  /* printf("%.3f %.3f\n%.3f %.3f\n%.3f %.3f\n", a, b, c, d, e, f); */

  Pi0 = Hv[3]*b+Hv[0]*a + Pi0;
  Pi1 = Hv[4]*b+Hv[1]*a + Pi1;
  Pi2 = Hv[5]*b+Hv[2]*a + Pi2;
  Pi3 = Hv[3]*d+Hv[0]*c + Pi3;
  Pi4 = Hv[4]*d+Hv[1]*c + Pi4;
  Pi5 = Hv[5]*d+Hv[2]*c + Pi5;
  Pi6 = Hv[3]*f+Hv[0]*e + Pi6;
  Pi7 = Hv[4]*f+Hv[1]*e + Pi7;
  Pi8 = Hv[5]*f+Hv[2]*e + Pi8;

  A = Pi4 * Pi8 - Pi5 * Pi7;
  B = -Pi3 * Pi8 + Pi5 * Pi6;
  C = Pi3 * Pi7 - Pi4 * Pi6;
  inv_det = 1.0 / (Pi0 * A + Pi1 * B + Pi2 * C);

  P[0] = inv_det * A;
  P[3] = inv_det * B;
  P[6] = inv_det * C;

  P[1] = (-Pi1 * Pi8 + Pi2 * Pi7) * inv_det; // D
  P[4] = (Pi0 * Pi8 - Pi2 * Pi6) * inv_det; // E
  P[7] = (-Pi0 * Pi7 + Pi1 * Pi6) * inv_det; // F

  P[2] = (Pi1 * Pi5 - Pi2 * Pi4) * inv_det; // G
  P[5] = (-Pi0 * Pi5 + Pi2 * Pi3) * inv_det; // H
  P[8] = (Pi0 * Pi4 - Pi1 * Pi3) * inv_det; // I

  /*   x += particle.P @ Hv.T @ Sfi @ dz  # proposal mean */
  a = Hv[2]*P[2]+Hv[1]*P[1]+Hv[0]*P[0];
  b = Hv[5]*P[2]+Hv[4]*P[1]+Hv[3]*P[0];
  c = Hv[2]*P[5]+Hv[1]*P[4]+Hv[0]*P[3];
  d = Hv[5]*P[5]+Hv[4]*P[4]+Hv[3]*P[3];
  e = Hv[2]*P[8]+Hv[1]*P[7]+Hv[0]*P[6];
  f = Hv[5]*P[8]+Hv[4]*P[7]+Hv[3]*P[6];

  double g = Sfi2*b+Sfi0*a;
  double h = Sfi3*b+Sfi1*a;
  double i = Sfi2*d+Sfi0*c;
  double j = Sfi3*d+Sfi1*c;
  double k = Sfi2*f+Sfi0*e;
  double l = Sfi3*f+Sfi1*e;

  x[0] += dz[1]*h+dz[0]*g;
  x[1] += dz[1]*j+dz[0]*i;
  x[2] += dz[1]*l+dz[0]*k;

  Py_INCREF(Py_None);
  return Py_None;
}


static PyObject *compute_weight(PyObject *self, PyObject *args)
{
  PyArrayObject *Sf_ = 0;
  PyArrayObject *z_ = 0;
  PyArrayObject *zp_ = 0;

  if (!PyArg_ParseTuple(args, "O!O!O!",
                        &PyArray_Type, &Sf_, &PyArray_Type, &z_, &PyArray_Type, &zp_))
    {
      return NULL;
    }
  double const *Sf = PyArray_DATA(Sf_);
  double const *z = PyArray_DATA(z_);
  double const *zp = PyArray_DATA(zp_);


  double det = (Sf[0] * Sf[3] - Sf[1] * Sf[2]);
  if (det == 0.0)
    return Py_BuildValue("d", 1.0);

  double dz0 = z[0] - zp[0];
  double dz1 = pi2pi(z[1] - zp[1]);

  /* printf("z: %.3f %.3f\t dz: %.3f %.3f\n", z[0], z[1], dz0, dz1); */

  double inv_det = 1.0 / det; 
  double Sfi0 = Sf[3] * inv_det;
  double Sfi1 = -Sf[1] * inv_det;
  double Sfi2 = -Sf[2] * inv_det;
  double Sfi3 = Sf[0] * inv_det;

  double num = exp(-0.5 * (dz1 * (Sfi3*dz1+Sfi2*dz0) + dz0 * (Sfi1*dz1+Sfi0*dz0)));
  double den = 2.0 * M_PI * sqrt(det);
 
  return Py_BuildValue("d", num / den);
}

static PyObject *pi_2_pi(PyObject *self, PyObject *args)
{

  double angle;
  if (!PyArg_ParseTuple(args, "d",
                        &angle))
    {
      return NULL;
    }
 
  return Py_BuildValue("d", pi2pi(angle));
}

static PyMethodDef simslam_methods[] =
  {
   {"compute_jacobians_fast", compute_jacobians, METH_VARARGS, "Compute Jacobians."},
   {"update_kf_with_cholesky_fast", update_kf_with_cholesky, METH_VARARGS, "Update KF with Cholesky decomposition."},
   {"proposal_sampling_fast", proposal_sampling, METH_VARARGS, ""},
   {"compute_weight_fast", compute_weight, METH_VARARGS, ""},   
   {"pi_2_pi", pi_2_pi, METH_VARARGS, ""},   

   {NULL, NULL, 0, NULL}        /* Sentinel */
  };


static struct PyModuleDef moduledef =
  {
   PyModuleDef_HEAD_INIT,
   "simslam",
   "Functions for SLAM. Copyright (c) Kirill Sidorov and Cardiff Racing Driverless, 2019.",
   -1,
   simslam_methods,
   NULL, NULL, NULL, NULL
  };


PyMODINIT_FUNC PyInit_simslam()
{
  import_array();
  return PyModule_Create(&moduledef);
}
