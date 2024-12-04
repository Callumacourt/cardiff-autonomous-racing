if 0
    fn = list_files('../data/cones/amz/every10/*.png');
    am = load('yb_vs_bg_33x25_90_gray.mat', '-mat');
    svm_alphas = am.svm.Alpha .* am.svm.SupportVectorLabels;
    svm_vectors = am.svm.SupportVectors';
    svm_bias = am.svm.Bias;
end

if 0
net = feedforwardnet([20 10], 'trainscg');
net.divideParam.trainRatio = 80/100;
net.divideParam.valRatio = 10/100;
net.divideParam.testRatio = 10/100;
% net.performParam.regularization = 0.5;
net.trainParam.max_fail = 15;
net.trainParam.epochs = 20;
net.trainParam.showCommandLine = true;
net.trainParam.show = 1;
end

first = true;
for imidx = 35:numel(fn)
    
    im = rgb2gray(imread(fn{imidx}));
    T = project_image(im, am);
    tic
    T = T(:, 1:17:end);
    svm_pred = kssvmpredict(T, svm_vectors, svm_alphas, svm_bias);
    toc
    
%     if first
        net = train(net, T, svm_pred);
%         first = false;
%     else
%         net = adapt(net, T, svm_pred);
        
%     end
end
