% x = load('svm_training_b.mat'); data = x.data; lab = x.lab;

K = 5;
c = cvpartition(size(data, 1), 'KFold', K);

bc_steps = 3:16;
sigma_steps = -1.5:0.125:0;

bc = 2.^bc_steps;
sigma = 2.^sigma_steps;

[X, Y] = meshgrid(bc_steps, sigma_steps);
E = nan(numel(sigma), numel(bc));
N = nan(numel(sigma), numel(bc));
RECALL = nan(numel(sigma), numel(bc));
for i = 1:numel(bc)
    for j = 1:numel(sigma)
        CONF = zeros(2);
        for fold = 1:1
            svm = fitcsvm(data(c.training(fold), :), lab(c.training(fold)), ...
                'KernelFunction', 'gaussian', 'Standardize', false, 'CrossVal', 'off', ...
                'BoxConstraint', bc(i), 'KernelScale', sigma(j), 'NumPrint', 100, 'Verbose', 0, ...
                'OutlierFraction', 0.0);
            [pred, scores] = predict(svm, data(c.test(fold), :));
            fprintf('%d support vectors.\n', nnz(svm.IsSupportVector));
            conf = confusion(lab(c.test(fold)), pred);
            [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf);
            fprintf('Fold %d: recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
                fold, recall * 100, specificity * 100, precision * 100, ...
                F1 * 100, accuracy * 100, balanced_accuracy * 100);
            CONF = CONF + conf;
        end
%         fprintf('Training full SVM...\n');
%         svm = fitcsvm(data, lab, ...
%             'KernelFunction', 'gaussian', 'Standardize', false, 'CrossVal', 'off', ...
%             'BoxConstraint', bc(i), 'KernelScale', sigma(j), 'OutlierFraction', 0.0);
%         fprintf('%d support vectors.\n', nnz(svm.IsSupportVector));
        
        E(j, i) = CONF(2, 1) + CONF(1, 2);
        N(j, i) = nnz(svm.IsSupportVector);
        RECALL(j, i) = CONF(2, 2) / (CONF(2, 2) + CONF(2, 1));
        fig(1); surf(X, Y, E); 
        xlabel('C'); ylabel('\sigma');
        fig(2); surf(X, Y, N); 
        xlabel('C'); ylabel('\sigma');
        fig(3); surf(X, Y, RECALL); 
        xlabel('C'); ylabel('\sigma');
        
        drawnow;
        E
        RECALL
        N

    end
end
