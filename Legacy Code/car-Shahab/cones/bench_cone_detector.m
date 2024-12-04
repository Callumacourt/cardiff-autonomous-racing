if 0
    fprintf('Loading annotations...\n');
    [imfn, bb] = load_annotated_cones();
    detector = vision.CascadeObjectDetector('cone_detector.xml');
end

detector.ScaleFactor = 1.1;
detector.MergeThreshold = 15;

CONF = zeros(2);
DIST = [];
IOU = [];
for i = 465:numel(imfn)
    fprintf('%d / %d\n', i, numel(imfn));
    im = imread(imfn{i});
    [conf, dist, iou] = bench_cone_detection_image(im, detector, ...
                                                   bb{i}(:, 2:end), ...
                                                   'visualise', true);
    CONF = CONF + conf;
    DIST = [DIST dist];
    IOU = [IOU iou];
    
    if max(dist) > 50, break; end
end
