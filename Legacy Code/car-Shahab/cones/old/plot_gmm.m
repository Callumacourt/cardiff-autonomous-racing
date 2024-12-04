function plot_gmm(gmm, colour)

for i = 1:gmm.NumComponents
    e1 = plot_gaussian_ellipsoid(gmm.mu(i, :), gmm.Sigma(:, :, i), 2);
    set(e1, 'FaceColor', colour, 'EdgeColor', colour, 'FaceAlpha', 0.2, 'EdgeAlpha', 0.4, 'LineWidth', 2);
end