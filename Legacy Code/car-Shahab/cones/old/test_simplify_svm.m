if 1
    x = load('svm_training_b.mat'); data = x.data; lab = x.lab;
    K = 5;
    c = cvpartition(size(data, 1), 'KFold', K);
    
    svm = fitcsvm(data, lab, ...
        'KernelFunction', 'gaussian', 'Standardize', false, 'CrossVal', 'off', ...
        'BoxConstraint', 8, 'KernelScale', 0.3242, 'OutlierFraction', 0.0);
    
    [pred, scores] = predict(svm, data);
    N = nnz(svm.IsSupportVector);
    fprintf('%d support vectors.\n', N);
    conf = confusion(lab, pred);
    [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf);
    fprintf('[%d]: recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
        N, recall * 100, specificity * 100, precision * 100, ...
        F1 * 100, accuracy * 100, balanced_accuracy * 100);
    
    E0 = conf(1, 2) + conf(2, 1);
end

N = [10:40];
E = zeros(size(N));
for i = 1:numel(N)
    best_err = inf;
    for iter = 1:10
        [svm_vectors, svm_alphas, svm_bias] = simplify_svm(svm, N(i));
        
        scale = single(svm.KernelParameters.Scale);
        pred1 = kssvmpredict(single(data)' / scale, svm_vectors / scale, svm_alphas, svm_bias);
        conf = confusion(lab, pred1' > 0);
        [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf);
        fprintf('[%d]: recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
            N(i), recall * 100, specificity * 100, precision * 100, ...
            F1 * 100, accuracy * 100, balanced_accuracy * 100);
        err = conf(1, 2) + conf(2, 1);
        if err < best_err
            best_err = err;
        end
    end
    E(i) = best_err;
    fig(1);
    
    plot(N, E);
    hold on
    hline(E0, 'g');
    hold off
    drawnow;
end
