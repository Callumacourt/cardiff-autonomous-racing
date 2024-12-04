am = load('yb_vs_bg_33x25_90_gray.mat', '-mat');
svm_alphas = am.svm.Alpha .* am.svm.SupportVectorLabels;
svm_vectors = am.svm.SupportVectors';
svm_bias = am.svm.Bias;
im = imread('../data/cones/amz/every10/000005.png');
% im = imread('../data/cones/amz/every10/000345.png');
im = rgb2gray(im);

% imr = im(:, :, 1);
% img = im(:, :, 2);
% imb = im(:, :, 3);
% imdr = single(imr);
% imdg = single(img);
% imdb = single(imb);
imd = single(im);

ch = 1;

[h, w, d] = size(im);
scale = 1.0;
if 0
    Ty = zeros(am.keep, h * w, numel(scale));
    B = am.B(:, 1:am.keep);
    tproj = tic;
    buf = zeros(am.ch, am.cw);
    bufr = zeros(am.ch, am.cw);
    bufg = zeros(am.ch, am.cw);
    bufb = zeros(am.ch, am.cw);
    
    count = 1;
    %     a = ones(size(am.a));
    %     b = zeros(size(am.b));
    for col = 1:1:w
        x = col - (am.cw * scale - 1) / 2;
        for row = 1:1:h
            y = row - (am.ch * scale - 1) / 2;
            getwndbl_scale(buf, im, x, y, am.cw * scale, am.ch * scale);
            %             getwndbl_scale(bufr, imr, x, y, am.cw * scale, am.ch * scale);
            %             getwndbl_scale(bufg, img, x, y, am.cw * scale, am.ch * scale);
            %             getwndbl_scale(bufb, imb, x, y, am.cw * scale, am.ch * scale);
            %             buf = [bufr(:); bufg(:); bufb(:)];
            
            
            Ty(:, count) = am_project(buf(:), B, am.avg, am.a, am.b);
            count = count + 1;
        end
    end
    dtproj = toc(tproj);
    fprintf('Projection: %.3f sec.\n', dtproj);
end
C = reshape(Ty(1, :), h, w);

fig(1); sc(C);
% [min(C(:)) max(C(:))]


tic
T = project_image(im, am);
toc

F = reshape(T(1, :), h, w);
fig(2); sc(F);
% [min(F(:)) max(F(:))]

max(max(abs(C - F)))
fig(3); sc(C - F)

max(max(abs(T - Ty)))

