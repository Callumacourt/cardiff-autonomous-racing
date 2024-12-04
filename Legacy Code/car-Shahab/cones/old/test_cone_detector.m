if 0
    fprintf('Loading annotations...\n');
    [imfn, bb] = load_annotated_cones();
end
detector = vision.CascadeObjectDetector('cone_detector_yb_pad125_8x7.xml');
detector.ScaleFactor = 1.15;
detector.MergeThreshold = 1;
detector.MaxSize = [32 24] * 2;

gt_col = [0 255 0];

idx = 42;
im = imread(imfn{idx});
img = rgb2gray(im(1:h, :, :));
lab = bb{idx}(:, 2:end);

[h, w, d] = size(im);

% Detect cones
tic
bbox = step(detector, img);
toc


% Plot bboxes
im = draw_bbox(im, bbox, [255 0 0], 1);
% im = draw_bbox(im, lab, gt_col, 0.5);

fig(1); sc(im);
