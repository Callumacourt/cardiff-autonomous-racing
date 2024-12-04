opt.negative_folder = '../data/negative/';
fn = dirPlus(opt.negative_folder, ...
    'FileFilter', '\.(jpg|jpeg|png)$', ...
    'ValidateDirFcn', @(x) (isempty(strfind(x.name, 'all'))));
detector = vision.CascadeObjectDetector('cone_detector_haar_yb_pad125_12x10_st25_far0.500_tpr0.999_nsf2.0.xml');
detector.ScaleFactor = 1.1;
detector.MergeThreshold = 1;
detector.MinSize = [12 10];
detector.MaxSize = [12 10] * 6;

for i = 1:numel(fn)
    im = imread(fn{i});
    img = rgb2gray(im);
    tic
    bbox = step(detector, img);
    toc
    if ~isempty(bbox)
        im = draw_bbox(im, bbox, [0 255 0], 1);
        fig(1); sc(im);
        imwrite(im, sprintf('out/negative/%05d.png', i));
    end
end
