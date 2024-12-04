function [svm_vectors, svm_alphas, svm_bias] = simplify_svm(svm, N)

model.fun = 'svmclass';
model.Alpha = -svm.Alpha .* svm.SupportVectorLabels;
model.b = -svm.Bias;
model.nsv = nnz(svm.IsSupportVector);
model.sv = struct;
model.sv.X = svm.SupportVectors';
model.options = struct;
model.options.ker = 'rbf';
model.options.arg = svm.KernelParameters.Scale * sqrt(0.5);
% model.options.C = 10;

compact_model = rsrbf(model, struct('nsv', N, 'eps', 1e-6, 'verb', 0));

svm_vectors = single(compact_model.sv.X);
svm_alphas = single(-compact_model.Alpha);
svm_bias = single(-compact_model.b);


% % load training data
% trn = load('riply_trn');
% tst = load('riply_tst');
% % train SVM classifier
% model = smo(trn,struct('ker','rbf','arg',1,'C',10));
% 
% svm = fitcsvm(trn.X', trn.y', ...
%     'KernelFunction', 'gaussian', 'Standardize', false, 'CrossVal', 'off', ...
%     'BoxConstraint', 1, 'KernelScale', 1, 'NumPrint', 100, 'Verbose', 0, ...
%     'OutlierFraction', 0.0, 'Solver', 'SMO');
% 
% pred = predict(svm, tst.X');
% 
% conf = confusion(tst.y' - 1, pred - 1)
% [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf);
% fprintf('Fold %d: recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
%     1, recall * 100, specificity * 100, precision * 100, ...
%     F1 * 100, accuracy * 100, balanced_accuracy * 100);
% 
% pred1 = svmclass(tst.X, model);
% conf1 = confusion(tst.y' - 1, pred1' - 1)
% [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf1);
% fprintf('Fold %d: recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
%     1, recall * 100, specificity * 100, precision * 100, ...
%     F1 * 100, accuracy * 100, balanced_accuracy * 100);
% 
% 
% model.fun = 'svmclass';
% model.Alpha = -svm.Alpha .* svm.SupportVectorLabels;
% model.b = -svm.Bias;
% model.nsv = nnz(svm.IsSupportVector);
% model.sv = struct;
% model.sv.X = svm.SupportVectors';
% model.options = struct;
% model.options.ker = 'rbf';
% model.options.arg = sqrt(0.5);
% model.options.C = 10;
% 
% 
% pred2 = svmclass(tst.X, model);
% conf2 = confusion(tst.y' - 1, pred2' - 1)
% [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf2);
% fprintf('Fold %d: recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
%     1, recall * 100, specificity * 100, precision * 100, ...
%     F1 * 100, accuracy * 100, balanced_accuracy * 100);
% 
% % model = model;
% % return
% 
% 
% % compute the reduced rule with 10 support vectors
% compact_model = rsrbf(model,struct('nsv',10));
% 
% 
% pred3 = svmclass(tst.X, compact_model);
% conf3 = confusion(tst.y' - 1, pred3' - 1)
% [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf1);
% fprintf('Fold %d: recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
%     1, recall * 100, specificity * 100, precision * 100, ...
%     F1 * 100, accuracy * 100, balanced_accuracy * 100);
% 
% svm_vectors = single(compact_model.sv.X);
% svm_alphas = single(-compact_model.Alpha);
% svm_bias = single(-compact_model.b);
% 
% % svm_vectors = single(svm.SupportVectors');
% % svm_alphas = single(svm.Alpha .* svm.SupportVectorLabels);
% % svm_bias = single(svm.Bias);
% pred4 = kssvmpredict(single(tst.X), svm_vectors, svm_alphas, svm_bias);
% pred4 = pred4 > 0;
% 
% conf4 = confusion(tst.y' - 1, pred4')
% [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf4);
% fprintf('Fold %d: recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
%     1, recall * 100, specificity * 100, precision * 100, ...
%     F1 * 100, accuracy * 100, balanced_accuracy * 100);
% 
% 
% return
% 
% % visualize decision boundaries
% fig(1); clf; 
% ppatterns(trn);
% h1 = pboundary(model,struct('line_style','r'));
% h2 = pboundary(red_model,struct('line_style','b'));
% legend([h1(1) h2(1)],'Original SVM','Reduced SVM');
% 
% 
% % evaluate SVM classifiers
% ypred = svmclass(tst.X,model);
% err = cerror(ypred,tst.y);
% red_ypred = svmclass(tst.X,model);
% 
% red_err = cerror(red_ypred,tst.y);
% fprintf(['Original SVM: nsv = %d, err = %.4f\n' ...
%     'Reduced SVM: nsv = %d, err = %.4f\n'], ...
%     model.nsv, err, red_model.nsv, red_err);
