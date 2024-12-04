function [p3d, err] = triangulate_point_new(x0, x1, P0, P1, I0, I1, pose1, E)

pose0 = [1 0 0 0; 0 1 0 0; 0 0 1 0];
x0n = unhomo_slow(inv(I0') * homo_slow(x0));
x1n = unhomo_slow(inv(I1') * homo_slow(x1));

p3d = triangulate(pose0, pose1, E, x0n, x1n);

x0_ = project_points(p3d', P0);
x1_ = project_points(p3d', P1);

err = [vnorm(x0 - x0_) vnorm(x1 - x1_)];
