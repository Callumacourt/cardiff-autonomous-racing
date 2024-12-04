am = load('am_y_vs_bg_26x21_95_rgb.mat');
% X = rand([am.ch * am.cw * 3, 100000], 'single');
% B = single(am.B); avg = single(am.avg); a = single(am.a); b = single(am.b);
% x = (B' * subcol(X, avg))';
% x = x .* repmat(a, size(proj, 1), 1) + ...
%     repmat(b, size(proj, 1), 1);

x = rand(1000, am.keep) * 1;
svm = am.svm;
x = single(x);
tic
[pred, scores] = predict(svm, x);
toc
f = scores(:, 2)';

svm_alphas = single(svm.Alpha .* svm.SupportVectorLabels);
svm_vectors = single(svm.SupportVectors');
svm_bias = single(svm.Bias);
xx = single(x');

tic
f1 = kssvmpredict(xx, svm_vectors, svm_alphas, svm_bias);
toc
max(abs(f - f1))

% xx = xx(:, 1);
% x = x(1, :);
% iter = 100000;
% 
% % tic
% % for i = 1:iter
% %     [pred, scores] = predict(svm, x);
% %     f2 = scores(2);
% % end
% % toc
% 
% tic
% for i = 1:iter
%     f3 = kssvmpredict(xx, svm_vectors, svm_alphas, svm_bias);
% end
% toc
% abs(f3 - f(1))
