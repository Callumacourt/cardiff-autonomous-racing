opt.ch = 26;
opt.cw = 21;
opt.colour = true;
opt.labels = [0, 1];
opt.pad = [];
kernel_scale = 1.0;

if 0
    fprintf('Loading positive examples from annotations...');
    [Xpos, L, Xother, fn] = load_positive_patches(opt.labels, 'cw', opt.cw, 'ch', opt.ch, ...
        'colour', opt.colour, 'pad', opt.pad);
    fprintf('done\n');
end

if 0
    % Load negative patches
    fprintf('Loading negative examples...');
    Xneg = load('patches_26_21_neg_rgb_100000'); Xneg = Xneg.Xneg(:, 1:10:end);
    Xneg_mined = load('patches_26_21_neg_rgb_89179_mined'); Xneg_mined = Xneg_mined.Xneg(:, 1:1:end);
    Xneg = [Xneg Xother Xneg_mined];
    fprintf('done\n');
    % Resize if necessary
    if size(Xneg, 1) ~= opt.ch * opt.cw * 3
        Xneg = resize_patches(Xneg, opt.ch, opt.cw, opt.ch, opt.cw, opt.colour);
    end
end

lab = [ones(1, size(Xpos, 2)) zeros(1, size(Xneg, 2))]';
X = [Xpos Xneg]';
% Noralise data to [0, 1]
X_min = min(X, [], 2);
X_max = max(X, [], 2);
a = 1 ./ (X_max - X_min);
b = -X_min .* a;
data = bsxfun(@plus, bsxfun(@times, X, a), b);

opt.K = 5;
opt.C = 8;
opt.kernel_scale = 1.0;
opt.cost = [0 1; 10 0];
opt.validate = true;
c = cvpartition(size(data, 1), 'KFold', opt.K);
CONF = zeros(2);

if opt.validate
    fprintf('%d-fold validation...\n', opt.K);
    
    for fold = 1:opt.K
        svm = fitcsvm(data(c.training(fold), :), lab(c.training(fold)), ...
            'KernelFunction', 'linear', 'Standardize', false, 'CrossVal', 'off', ...
            'BoxConstraint', opt.C, 'KernelScale', opt.kernel_scale, 'NumPrint', 100, 'Verbose', 1, ...
            'OutlierFraction', 0.0, 'Solver', 'ISDA', 'Cost', opt.cost);
        [pred, ~] = predict(svm, data(c.test(fold), :));
        fprintf('%d support vectors.\n', nnz(svm.IsSupportVector));
        
        
        lab = lab(:);
        conf = confusion(lab(c.test(fold)), pred);
        [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf);
        fprintf('Fold %d: recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
            fold, recall * 100, specificity * 100, precision * 100, ...
            F1 * 100, accuracy * 100, balanced_accuracy * 100);
        CONF = CONF + conf;
    end
    [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(CONF);
    fprintf('\nOVERALL: recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
        recall * 100, specificity * 100, precision * 100, ...
        F1 * 100, accuracy * 100, balanced_accuracy * 100);
    CONF %#ok<NOPRT>
end