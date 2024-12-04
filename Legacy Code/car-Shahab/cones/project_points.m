function points2d = project_points(points3d, P)
points3dHomog = [points3d, ones(size(points3d, 1), 1, 'like', points3d)]';
points2dHomog = P * points3dHomog;
points2d = bsxfun(@rdivide, points2dHomog(1:2, :), points2dHomog(3, :));