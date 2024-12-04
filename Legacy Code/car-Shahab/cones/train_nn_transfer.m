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
    L = kssvmpredict(data, svmy_vectors, svmy_alphas, svmy_bias);
end

fn = list_files('../data/cones/amz/every10/*.png');

for imidx = 1%1:10:numel(fn)
    
    im = imread(fn{imidx});
    [h, w, d] = size(im);
    
    if d == 3 && ~opt.colour
        img = rgb2gray(im);
    else
        imr = im(:, :, 1);
        img = im(:, :, 2);
        imb = im(:, :, 3);
    end
    step = 8;
    cw = 24; ch = 32;
    
    
    s1 = 0.25;
    s2 = 2.5;
    n = 6;
    a = (s2 / s1) ^ (1/(n-1));
    scale = s1 * a.^(0:n-1);
    
    scale = [0.25 0.5 1.0 1.5 2.5];
%     scale = 1.5;
    % scale = [0.75 1.5];
    Dy = zeros(h/2, w/2, numel(scale));
    Db = zeros(h/2, w/2, numel(scale));
    buf = zeros(ch, cw);
    bufr = zeros(ch, cw);
    bufg = zeros(ch, cw);
    bufb = zeros(ch, cw);
    t1 = tic;
    
    
    % Project
    if 1
        Ty = zeros(amy.keep, h/2 * w/2, numel(scale));
        Tb = zeros(amb.keep, h/2 * w/2, numel(scale));
        for s = 1:numel(scale)
            tproj = tic;
            fprintf('Scale %.3f\n', scale(s));
            
            count = 1;
            for col = 1:2:w
                x = col - (cw * scale(s) - 1) / 2;
                for row = 1:2:h
                    y = row - (ch * scale(s) - 1) / 2;
                    
                    if opt.colour
                        getwndbl_scale(bufr, imr, x, y, cw * scale(s), ch * scale(s));
                        getwndbl_scale(bufg, img, x, y, cw * scale(s), ch * scale(s));
                        getwndbl_scale(bufb, imb, x, y, cw * scale(s), ch * scale(s));
                        buf = [bufr(:); bufg(:); bufb(:)];
                    else
                        getwndbl_scale(buf, img, x, y, cw * scale(s), ch * scale(s));
                    end
                    
                    % TODO: same projection
                    Ty(:, count, s) = am_project(buf, amy.B, amy.avg, amy.a, amy.b);
                    count = count + 1;
                end
            end
            dtproj = toc(tproj);
            fprintf('Projection: %.3f sec.\n', dtproj);
            
        end
    end
    for i = 1:size(Ty, 3)
        l = kssvmpredict(Ty(:, :, i), svmy_vectors, svmy_alphas, svmy_bias);
        data = [data Ty(:, :, i)];
        L = [L l];
    end
end



if 0
    net = feedforwardnet([10 10], 'trainbr');
    net.divideParam.trainRatio = 80/100;
    net.divideParam.valRatio = 10/100;
    net.divideParam.testRatio = 10/100;
    % net.performParam.regularization = 0.5;
    net.trainParam.max_fail = 15;
    net.trainParam.epochs = 150;
    net.trainParam.showCommandLine = true;
    
    t = zeros(2, numel(lab));
    t(1, lab == 0) = 1;
    t(2, lab == 1) = 1;
    net = train(net, data', L, 'showResources', 'yes');
end
