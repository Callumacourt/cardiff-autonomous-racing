if 0
pos = load('pos.mat'); pos = pos.proj;
neg = load('neg.mat'); neg = neg.proj_neg;
data = [pos; neg];
lab = [ones(1, size(pos, 1)) zeros(1, size(neg, 1))];
clear pos; clear neg;
end
c = cvpartition(size(data, 1), 'KFold', 5);
CONF = zeros(2);
for fold = 1:5
%     svm = fitcsvm(data(c.training(1), :), lab(c.training(1)), ...
%         'KernelFunction', 'rbf', 'Standardize', false, 'CrossVal', 'off', ...
%         'BoxConstraint', 8, 'Nu', 0.5);
    
%     cl = fitcdiscr(data(c.training(1), :), lab(c.training(1)), ...
%         'DiscrimType', 'quadratic');
%     cl = fitcnb(data(c.training(1), :), lab(c.training(1)));

    cl = fitctree(data(c.training(1), :), lab(c.training(1)), ...
        'AlgorithmForCategorical', 'Exact', ...
        'Prune', 'off');

    tic
    [pred, scores] = predict(cl, data(c.test(fold), :));
    toc
    lab = lab(:);
    
    conf = zeros(2);
    conf(1, 1) = nnz(lab(c.test(fold)) == 0 & pred == 0);
    conf(1, 2) = nnz(lab(c.test(fold)) == 0 & pred == 1);
    conf(2, 1) = nnz(lab(c.test(fold)) == 1 & pred == 0);
    conf(2, 2) = nnz(lab(c.test(fold)) == 1 & pred == 1);
    
    [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf);
    fprintf('Fold %d: recall: %.1f%%, spec: %.1f%%, prec: %.1f%%,\nF1: %.1f%%, acc: %.1f%%, bacc: %.1f%%\n', ...
        fold, recall * 100, specificity * 100, precision * 100, ...
        F1 * 100, accuracy * 100, balanced_accuracy * 100);
    CONF = CONF + conf;
end
[recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(CONF);
fprintf('\nOVERALL: recall: %.1f%%, spec: %.1f%%, prec: %.1f%%,\nF1: %.1f%%, acc: %.1f%%, bacc: %.1f%%\n', ...
    recall * 100, specificity * 100, precision * 100, ...
    F1 * 100, accuracy * 100, balanced_accuracy * 100);

CONF
