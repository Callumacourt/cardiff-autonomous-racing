am = load('models/am_svm/am_yb_vs_bg_26x21_90_c_rgb.mat');

X = rand([am.ch * am.cw * 3, 100000], 'single');
B = single(am.B); avg = single(am.avg); a = single(am.a); b = single(am.b);


tic
proj = (B' * subcol(X, avg))';
proj = proj .* repmat(a, size(proj, 1), 1) + ...
    repmat(b, size(proj, 1), 1);
toc

tic
proj1 = am_project(X, B, avg, a, b);
toc

% tic
% proj2 = am_project_eigen(X, B, avg, a, b);
% toc

max(max(abs(proj' - proj1)))
% max(max(abs(proj' - proj2)))
