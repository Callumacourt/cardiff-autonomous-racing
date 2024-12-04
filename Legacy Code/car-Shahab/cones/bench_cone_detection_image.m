function [conf, dist, iou] = bench_cone_detection_image(im, detector, lab, varargin)

opt.visualise = false;
opt = parseargs(opt, varargin{:});

gt_col = [0 255 0];

[h, w, d] = size(im);

% Detect cones
tic
bbox = step(detector, im);
toc

% Remove padding
pad = 6;
bbox(:, 1) = bbox(:, 1) + pad;
bbox(:, 2) = bbox(:, 2) + pad;
bbox(:, 3) = bbox(:, 3) - 2 * pad;
bbox(:, 4) = bbox(:, 4) - 2 * pad;



% Overall intersection over union of all bboxes
iou = intersection_over_union(h, w, lab, bbox);

% Pairwise intersetion over union
C = zeros(size(lab, 1), size(bbox, 1));
for i = 1:size(C, 1)
    for j = 1:size(C, 2)
        C(i, j) = -intersection_over_union(h, w, lab(i, :), bbox(j, :));
    end
end

[A, cost] = hungarian(C);

[row, col] = find(A);

% Compute bbox centroids
labc = bbox_centroids(lab);
bboxc = bbox_centroids(bbox);

pairs = [];
dist = [];
for i = 1:numel(row)
    if C(row(i), col(i)) > -0.25, continue; end
    d = vnorm(labc(:, row(i)) - bboxc(:, col(i)));
    % if d > 5, continue; end
    draw_line(im, labc(:, row(i)), bboxc(:, col(i)), [255 255 255], 1);
    pairs = [pairs [row(i); col(i)]];
    dist = [dist d];
end

tp = size(pairs, 2);
fn = size(lab, 1) - tp;
fp = size(bbox, 1) - tp;
% sensitivity = tp / (tp + fn);
% precision = tp / (tp + fp);
conf = [nan fp; fn tp]; 


if opt.visualise
% Plot bboxes
im = draw_bbox(im, bbox, [255 0 0], 1);
im = draw_bbox(im, lab, gt_col, 1);

% Plot bbox numbers
for i = 1:size(bbox, 1)
    im = insertText(im, bbox(i, 1:2) + [bbox(i, 3) 0.5 * bbox(i, 4)], ...
                    num2str(i), ...
                    'TextColor', [255 255 128], 'BoxColor', [255 128 128], ...
                    'AnchorPoint', 'LeftCenter', 'BoxOpacity', 0.25, ...
                    'Font', 'VL-Gothic-Regular', 'FontSize', 12);
end
for i = 1:size(lab, 1)
    im = insertText(im, lab(i, 1:2) + [0 0.5 * lab(i, 4)], ...
                    num2str(i), ...
                    'TextColor', [255 255 128], 'BoxColor', [128 255 128], ...
                    'AnchorPoint', 'RightCenter', 'BoxOpacity', 0.25, ...
                    'Font', 'VL-Gothic-Regular', 'FontSize', 12);
end

% Plot centroids
im = draw_cross(im, labc(1, :)', labc(2, :)', [0 255 0], 0.5);
im = draw_cross(im, bboxc(1, :)', bboxc(2, :)', [255 0 0], 0.5);

fig(1); sc(im);

% imwrite(im, 'im.png');
drawnow;
pairs
end
