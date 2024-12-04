function C = bbox_centroids(bbox)

C = [bbox(:, 1) + (bbox(:, 3) - 1) * 0.5 bbox(:, 2) + (bbox(:, 4) - 1) * 0.5]';
