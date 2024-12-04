function [point3d, reprojectionErrors] = triangulate_point(point1, point2, P1, P2)

% do the triangulation
A = zeros(4, 4);
A(1:2,:) = point1 * P1(3,:) - P1(1:2,:);
A(3:4,:) = point2 * P2(3,:) - P2(1:2,:);

[~,~,V] = svd(A);
X = V(:, end);
X = X/X(end);

point3d = X(1:3);

points1proj = project_points(point3d', P1);
points2proj = project_points(point3d', P2);
errors1 = hypot(point1(1,:)-points1proj(1,:), ...
    point1(2,:) - points1proj(2,:));
errors2 = hypot(point2(1,:)-points2proj(1,:), ...
    point2(2,:) - points2proj(2,:));

% reprojectionErrors = mean([errors1; errors2])';
reprojectionErrors = [errors1; errors2];
