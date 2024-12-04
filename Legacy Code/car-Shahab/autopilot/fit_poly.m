function p = fit_poly(points)


sample_size = 8; % number of points to sample per trial
if size(points, 2) < sample_size
    degree = 3;
    if size(points, 2) < 5, degree = 2; end
    p = polyfit(points(1, :), points(2, :), degree);
else
    max_inlier_dist = 0.3; % max allowable distance for inliers
    fit_poly_fn = @(points) polyfit(points(:, 1), points(:, 2), 3);
    eval_poly_fn = @(model, points) sum((points(:, 2) - polyval(model, points(:, 1))).^2, 2);
    [~, inlier_idx] = ransac(points', fit_poly_fn, eval_poly_fn, sample_size, max_inlier_dist);
    p = polyfit(points(1, inlier_idx), points(2, inlier_idx), 3);
end
