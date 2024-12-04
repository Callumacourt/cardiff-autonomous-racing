function  [svm_vectors, svm_alphas, svm_bias, svm_scale, conf, err] = train_svm(data, lab, varargin)

opt.simplify = true;
opt.Nsv = 30;
opt.replicates = 200;
opt.validate = true;
opt.K = 5;
opt.C = 64;
opt.kernel_scale = 2^-0.75;
opt.cost = [0 1; 1 0];
opt = parseargs(opt, varargin{:});

data = double(data);

c = cvpartition(size(data, 1), 'KFold', opt.K);
CONF = zeros(2);

if opt.validate
    fprintf('%d-fold validation...\n', opt.K);
    
    for fold = 1:opt.K
        svm = fitcsvm(data(c.training(fold), :), lab(c.training(fold)), ...
            'KernelFunction', 'gaussian', 'Standardize', false, 'CrossVal', 'off', ...
            'BoxConstraint', opt.C, 'KernelScale', opt.kernel_scale, 'NumPrint', 100, 'Verbose', 0, ...
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

fprintf('Training full SVM...\n');
svm = fitcsvm(data, lab, ...
    'KernelFunction', 'gaussian', 'Standardize', false, 'CrossVal', 'off', ...
    'BoxConstraint', opt.C, 'KernelScale', opt.kernel_scale, 'OutlierFraction', 0.0, ...
    'Cost', opt.cost);


%     am.svm = svm;
fprintf('%d support vectors in full SVM.\n', nnz(svm.IsSupportVector));

if opt.simplify
    best_err = inf;
    for iter = 1:opt.replicates
        [svm_vectors, svm_alphas, svm_bias] = simplify_svm(svm, opt.Nsv);
        pred = kssvmpredict(single(data)' / opt.kernel_scale, svm_vectors / opt.kernel_scale, svm_alphas, svm_bias);
        conf = confusion(lab, pred' > 0);
        err = conf(1, 2) + conf(2, 1);
        if err < best_err
            err %#ok<NOPRT>
            best_err = err;
            best_v = svm_vectors;
            best_a = svm_alphas;
            best_b = svm_bias;
        end
        
    end
    svm_vectors = single(best_v);
    svm_alphas = single(best_a);
    svm_bias = single(best_b);
    pred = kssvmpredict(single(data)' / opt.kernel_scale, svm_vectors / opt.kernel_scale, svm_alphas, svm_bias);
    conf = confusion(lab, pred' > 0) %#ok<NOPRT>
    [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf);
    fprintf('[%]: recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
        opt.Nsv, recall * 100, specificity * 100, precision * 100, ...
        F1 * 100, accuracy * 100, balanced_accuracy * 100);
else
    svm_alphas = single(svm.Alpha .* svm.SupportVectorLabels);
    svm_vectors = single(svm.SupportVectors');
    svm_bias = single(svm.Bias);
    conf = CONF;
    err = conf(1, 2) + conf(2, 1);
end
svm_scale = opt.kernel_scale;

