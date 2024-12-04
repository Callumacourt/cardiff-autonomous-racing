am = load('am_yb_vs_bg_26x21_90_c_rgb.mat');
im = imread('../data/local/amz/000001.png');
buf = zeros(am.ch, am.cw, size(im, 3), 'single');

B = am.B .* repmat(am.a, size(am.B, 1), 1);
svm_vectors = am.svm_vectors - repmat(am.b', 1, size(am.svm_vectors, 2)) + repmat(B' * am.avg, 1, size(am.svm_vectors, 2));
svm_alphas = am.svm_alphas;
svm_bias = am.svm_bias;
svm_scale = single(1.0 / (am.svm_scale * am.svm_scale));

C = zeros(size(im, 1), size(im, 2));

tic
for cy = 1:size(im, 1)
    cy
    y = cy; %cy - (am.ch - 1) * 0.5;
    for cx = 1:size(im, 2)
        x = cx; %cx - (am.cw - 1) * 0.5;
        C(cy, cx) = max(0, eval_bbox_multiscale(x, y, 16 * 4, im, buf, B, svm_vectors, svm_alphas, svm_bias, svm_scale));
    end
    if mod(cy, 10) == 0
        fig(1); sc(C);
        drawnow;
    end
end
toc

figure(1); clf;
sc(C);
% vnorm2 = vnorm(bsxfun(@minus, am.svm_vectors, proj1(:)));
% sum(am.svm_alphas .* (vnorm2 .^ 2)') + am.svm_bias
% fprintf('%f\n', sum(am.avg))
% fprintf('%f\n', sum(buf(:)))
% fprintf('%f\n', buf(15, 15, 1))
% fprintf('%f\n', sum(subcol(buf(:), am.avg)))
% (am.B' * subcol(buf(:), am.avg))'

% proj = (am.B' * subcol(buf(:), am.avg))';
% proj = proj .* repmat(am.a, size(proj, 1), 1) + ...
%     repmat(am.b, size(proj, 1), 1)


