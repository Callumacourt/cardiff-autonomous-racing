function [p3d, err] = triangulate_point_nonlin(point1, point2, P1, P2, h, w)

p3d = unhomo_slow(vgg_X_from_xP_nonlin([point1 point2], cat(3, P1, P2), [h h; w w]))';
x1 = project_points(p3d, P1);
x2 = project_points(p3d, P2);
err1 = vnorm(x1 - point1);
err2 = vnorm(x2 - point2);
err = [err1; err2];
