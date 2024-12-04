im = imread('recording/000173.jpg');
[~, im] = split_stereo_image(im);
ww = 48; wh = 64;

im = rgb2gray(im);
[h, w] = size(im);
det_fn = 'cone_detector.xml';
detector = vision.CascadeObjectDetector(det_fn, ...
    'MinSize', [wh ww], ...
    'MergeThreshold', 5);


C = zeros(h, w);
figure(1); clf;
for col = 1:w-ww+1
    col
    for row = 1:h-wh+1
        wnd = im(row:row+wh-1, col:col+ww-1);
        cone = step(detector, wnd);
        if isempty(cone), continue; end
        C(row + wh/2, col + ww/2) = 1;
    end
    if mod(col, 10) == 0
    sc(C); drawnow;
    end
end
