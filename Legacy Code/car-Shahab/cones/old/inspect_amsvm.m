lab = [L == 0 zeros(1, size(proj_neg, 1))]';
data = double([proj; proj_neg]);

kernel_scale = am.svm_scale;
scores = kssvmpredict(single(data)' / kernel_scale, am.svm_vectors / kernel_scale, am.svm_alphas, am.svm_bias);
pred = (scores > 0)';

conf = confusion(lab, pred) %#ok<NOPTS>
[recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf);
fprintf('Fold %d: recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
    1, recall * 100, specificity * 100, precision * 100, ...
    F1 * 100, accuracy * 100, balanced_accuracy * 100);

fp = find(lab == 0 & pred == 1);
fn = find(lab == 1 & pred == 0);

Xfn = X(:, fn);
Xall = [X Xother Xneg];
Xfp = Xall(:, fp);

figure(1); clf;
sc(reshape(Xfn, am.ch, am.cw, 3, []))

figure(2); clf;
sc(reshape(Xfp, am.ch, am.cw, 3, []))


lab = [L == 1 zeros(1, size(proj_neg, 1))]';
data = double([proj; proj_neg]);

kernel_scale = am.bsvm_scale;
scores = kssvmpredict(single(data)' / kernel_scale, am.bsvm_vectors / kernel_scale, am.bsvm_alphas, am.bsvm_bias);
pred = (scores > 0)';

conf = confusion(lab, pred) %#ok<NOPTS>
[recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf);
fprintf('Fold %d: recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
    1, recall * 100, specificity * 100, precision * 100, ...
    F1 * 100, accuracy * 100, balanced_accuracy * 100);

fp = find(lab == 0 & pred == 1);
fn = find(lab == 1 & pred == 0);

Xfn = X(:, fn);
Xneg = [Xother Xneg];
Xfp = Xneg(:, fp - size(X, 2));

figure(3); clf;
sc(reshape(Xfn, am.ch, am.cw, 3, []))

figure(4); clf;
sc(reshape(Xfp, am.ch, am.cw, 3, []))