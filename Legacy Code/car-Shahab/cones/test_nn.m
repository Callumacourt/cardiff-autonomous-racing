if 0
    pos = load('pos.mat'); pos = pos.proj;
    neg = load('neg.mat'); neg = neg.proj_neg;
    data = [pos; neg]';
    lab = [ones(1, size(pos, 1)) zeros(1, size(neg, 1))];
    clear pos; clear neg;
    
    amy = load('yellow_vs_bg.mat', '-mat');
    svmy_alphas = amy.svm.Alpha .* amy.svm.SupportVectorLabels;
    svmy_vectors = amy.svm.SupportVectors';
    svmy_bias = amy.svm.Bias;
    L = kssvmpredict(data', svmy_vectors, svmy_alphas, svmy_bias);
    
end
if 1
    
    
    net = feedforwardnet([20 10], 'trainbr');
    net.divideParam.trainRatio = 80/100;
    net.divideParam.valRatio = 10/100;
    net.divideParam.testRatio = 10/100;
    % net.performParam.regularization = 0.5;
    net.trainParam.max_fail = 15;
    net.trainParam.epochs = 150;
    net.trainParam.showCommandLine = true;
    net.trainParam.show = 1;


    t = zeros(2, numel(lab));
    t(1, lab == 0) = 1;
    t(2, lab == 1) = 1;
    net = train(net, data, L, 'showResources', 'yes');
end


return
in = Ty(:, 100);
a = net(in)

% 
% for iii = 1:numel(net.inputs{1}.processFcns)
%       x = feval( net.inputs{1}.processFcns{iii}, ...
%           'apply', in, net.inputs{1}.processSettings{iii} );
% end

t = net.inputs{1}.processSettings{1};
x = (in - t.xoffset) .* t.gain - 1;

x1 = tansig(net.IW{1} * x + net.b{1});
x2 = tansig(net.LW{2, 1} * x1 + net.b{2});
x3 = net.LW{3, 2} * x2 + net.b{3};

% for iii = 1:numel(net.outputs{3}.processFcns)
%      out = feval( net.outputs{3}.processFcns{iii}, ...
%           'reverse', x3, net.outputs{3}.processSettings{iii} );
% end
t = net.outputs{3}.processSettings{1};
out = (x3 + 1) ./ t.gain + t.xoffset
% 1 * k + b = hi
% -1 * k + b = low

% b = (hi + low)/2
% k = hi - (hi + low)/2
% 
% x3 * k + b
