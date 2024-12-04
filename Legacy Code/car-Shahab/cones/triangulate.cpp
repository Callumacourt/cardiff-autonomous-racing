#include "mex.h"
#include <Eigen/Cholesky>
#include <Eigen/Core>
#include <Eigen/Eigenvalues>
#include <Eigen/Geometry>
#include <Eigen/SVD>

using Eigen::Matrix;
using Eigen::MatrixXd;
using Eigen::Matrix3d;
using Eigen::Matrix4d;
using Eigen::Vector2d;
using Eigen::Vector3d;
using Eigen::Vector4d;
using Eigen::Map;

// Used as the projection matrix type.
typedef Eigen::Matrix<double, 3, 4> Matrix3x4d;


Eigen::Matrix3d CrossProductMatrix(const Vector3d& cross_vec) {
    Matrix3d cross;
    cross << 0.0, -cross_vec.z(), cross_vec.y(),
        cross_vec.z(), 0.0, -cross_vec.x(),
        -cross_vec.y(), cross_vec.x(), 0.0;
    return cross;
}

void EssentialMatrixFromTwoProjectionMatrices(
    const Matrix3x4d& pose1,
    const Matrix3x4d& pose2,
    Eigen::Matrix3d* essential_matrix) {
    // Create the Ematrix from the poses.
    const Eigen::Matrix3d R1 = pose1.leftCols<3>();
    const Eigen::Matrix3d R2 = pose2.leftCols<3>();
    const Eigen::Vector3d t1 = pose1.rightCols<1>();
    const Eigen::Vector3d t2 = pose2.rightCols<1>();

    // Pos1 = -R1^t * t1.
    // Pos2 = -R2^t * t2.
    // t = R1 * (pos2 - pos1).
    // t = R1 * (-R2^t * t2 + R1^t * t1)
    // t = t1 - R1 * R2^t * t2;

    // Relative transformation between to cameras.
    const Eigen::Matrix3d relative_rotation = R1 * R2.transpose();
    const Eigen::Vector3d translation = (t1 - relative_rotation * t2).normalized();
    *essential_matrix = CrossProductMatrix(translation) * relative_rotation;
}


// Given either a fundamental or essential matrix and two corresponding images
// points such that ematrix * point2 produces a line in the first image,
// this method finds corrected image points such that
// corrected_point1^t * ematrix * corrected_point2 = 0.
void FindOptimalImagePoints(const Matrix3d& ematrix,
                            const Vector2d& point1,
                            const Vector2d& point2,
                            Vector2d* corrected_point1,
                            Vector2d* corrected_point2) {
    const Vector3d point1_homog = point1.homogeneous();
    const Vector3d point2_homog = point2.homogeneous();

    // A helper matrix to isolate certain coordinates.
    Matrix<double, 2, 3> s_matrix;
    s_matrix << 1, 0, 0, 0, 1, 0;

    const Eigen::Matrix2d e_submatrix = ematrix.topLeftCorner<2, 2>();

    // The epipolar line from one image point in the other image.
    Vector2d epipolar_line1 = s_matrix * ematrix * point2_homog;
    Vector2d epipolar_line2 = s_matrix * ematrix.transpose() * point1_homog;

    const double a = epipolar_line1.transpose() * e_submatrix * epipolar_line2;
    const double b =
        (epipolar_line1.squaredNorm() + epipolar_line2.squaredNorm()) / 2.0;
    const double c = point1_homog.transpose() * ematrix * point2_homog;

    const double d = sqrt(b * b - a * c);

    double lambda = c / (b + d);
    epipolar_line1 -= e_submatrix * lambda * epipolar_line1;
    epipolar_line2 -= e_submatrix.transpose() * lambda * epipolar_line2;

    lambda *=
        (2.0 * d) / (epipolar_line1.squaredNorm() + epipolar_line2.squaredNorm());

    *corrected_point1 =
        (point1_homog - s_matrix.transpose() * lambda * epipolar_line1)
        .hnormalized();
    *corrected_point2 =
        (point2_homog - s_matrix.transpose() * lambda * epipolar_line2)
        .hnormalized();
}


// Triangulates 2 posed views
bool TriangulateDLT(const Matrix3x4d& pose1,
                    const Matrix3x4d& pose2,
                    const Vector2d& point1,
                    const Vector2d& point2,
                    Vector4d* triangulated_point) {
    Matrix4d design_matrix;
    design_matrix.row(0) = point1[0] * pose1.row(2) - pose1.row(0);
    design_matrix.row(1) = point1[1] * pose1.row(2) - pose1.row(1);
    design_matrix.row(2) = point2[0] * pose2.row(2) - pose2.row(0);
    design_matrix.row(3) = point2[1] * pose2.row(2) - pose2.row(1);

    // Extract nullspace.
    *triangulated_point =
        design_matrix.jacobiSvd(Eigen::ComputeFullV).matrixV().rightCols<1>();
    return true;
}

// Triangulates 2 posed views
bool Triangulate(const Matrix3x4d& pose1,
                 const Matrix3x4d& pose2,
		 const Eigen::Matrix3d& ematrix,
                 const Vector2d& point1,
                 const Vector2d& point2,
                 Vector4d* triangulated_point) {
    // Eigen::Matrix3d ematrix;
    // EssentialMatrixFromTwoProjectionMatrices(pose1, pose2, &ematrix);

    // mexPrintf("%.4f %.4f %.4f\n%.4f %.4f %.4f\n%.4f %.4f %.4f\n",
    // 	      ematrix(0, 0), ematrix(0, 1), ematrix(0, 2),
    // 	      ematrix(1, 0), ematrix(1, 1), ematrix(1, 2),
    // 	      ematrix(2, 0), ematrix(2, 1), ematrix(2, 2));
    Vector2d corrected_point1, corrected_point2;
    FindOptimalImagePoints(
        ematrix, point1, point2, &corrected_point1, &corrected_point2);

    // Now the two points are guaranteed to intersect. We can use the DLT method
    // since it is easy to construct.
    return TriangulateDLT(
        pose1, pose2, corrected_point1, corrected_point2, triangulated_point);
}



void mexFunction(int nlhs, mxArray *plhs[], int nrhs,
                 const mxArray *prhs[])
{
    if (nrhs != 5)
    {
        mexErrMsgTxt("Expected five arguments.\n");
    }

    // Camera matrices
    mxArray const *P0__ = prhs[0];
    double *P0_ = (double*)mxGetData(P0__);

    mxArray const *P1__ = prhs[1];
    double *P1_ = (double*)mxGetData(P1__);

    // Essential matrix
    mxArray const *E__ = prhs[2];
    double *E_ = (double*)mxGetData(E__);
    

    mxArray const *x0__ = prhs[3];
    double *x0_ = (double*)mxGetData(x0__);
    mwSize const* xdims = mxGetDimensions(x0__);
    int dim = xdims[0]; int N = xdims[1];

    mxArray const *x1__ = prhs[4];
    double *x1_ = (double*)mxGetData(x1__);


    Map<Eigen::Matrix<double, 3, 4>> P0(P0_);
    Map<Eigen::Matrix<double, 3, 4>> P1(P1_);
    Map<Eigen::Matrix<double, 3, 3>> E(E_);
    Map<Vector2d> x0(x0_);
    Map<Vector2d> x1(x1_);
    
    plhs[0] = mxCreateNumericMatrix(3, 1, mxDOUBLE_CLASS, mxREAL);
    double* result = (double*)mxGetData(plhs[0]);

    Vector4d X;
    Triangulate(P0, P1, E, x0, x1, &X);

    result[0] = X[0] / X[3];
    result[1] = X[1] / X[3];
    result[2] = X[2] / X[3];
}
