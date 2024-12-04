opt.name = 'yellow_vs_bg';


if 0
    amy = load('yellow_vs_bg.mat', '-mat');
    svmy_alphas = amy.svm.Alpha .* amy.svm.SupportVectorLabels;
    svmy_vectors = amy.svm.SupportVectors';
    svmy_bias = amy.svm.Bias;
    
    fprintf('Loading positive examples from annotations...\n');
    [X, L, Xother] = load_positive_patches();
    fprintf('done\n');
    
    % Load negative patches
    fprintf('Loading negative examples...\n');
    Xneg = load('patches_32_24_neg_rgb'); Xneg = Xneg.Xneg;
    Xneg = [Xneg Xother]; % Add cones of other colour
    clear Xfother
    clear Xother
    clear Xf
    
    lab = [ones(1, size(X, 2)) zeros(1, size(Xneg, 2))];
    X = [X Xneg];
    clear Xneg
end



if 0
    % Noralise data to [0, 1]
    X_min = min(X, [], 2);
    X_max = max(X, [], 2);
    a = 1 ./ (X_max - X_min);
    b = -X_min .* a;
    
    X = bsxfun(@plus, bsxfun(@times, X, a), b)';
    
    X = double(X);
    T = am_project(X, amy.B, amy.avg, amy.a, amy.b);
    svm_pred = kssvmpredict(T, svmy_vectors, svmy_alphas, svmy_bias);
end

if 0
    net = patternnet([40 20], 'trainscg');
    net.divideParam.trainRatio = 80/100;
    net.divideParam.valRatio = 10/100;
    net.divideParam.testRatio = 10/100;
    % net.performParam.regularization = 0.5;
    net.trainParam.max_fail = 15;
    net.trainParam.epochs = 500;
    net.trainParam.showCommandLine = true;
    net.trainParam.show = 1;
    
    
    t = zeros(2, numel(lab));
    t(1, lab == 0) = 1;
    t(2, lab == 1) = 1;
    net = train(net, X, t);
end


if 1
    %     amy = load('yellow_vs_bg.mat', '-mat');
    im = imread('../data/cones/amz/every10/000005.png');
    [h, w, d] = size(im);
    imr = im(:, :, 1);
    img = im(:, :, 2);
    imb = im(:, :, 3);
    scale = 1.0;
    Ty = zeros(ch * cw * 3, h, numel(scale));
    %     B = amy.B(1:amy.ch * amy.cw, 1);
    tproj = tic;
    buf = zeros(amy.ch, amy.cw);
    count = 1;
    a = ones(size(amy.a));
    b = zeros(size(amy.b));
    ch = amy.ch; cw = amy.cw;
    bufr = zeros(ch, cw);
    bufg = zeros(ch, cw);
    bufb = zeros(ch, cw);
    D = zeros(h, w);
    for col = 1:1:w
        col
        x = col - (amy.cw * scale - 1) / 2 + 0.5;
        for row = 1:1:h
            y = row - (amy.ch * scale - 1) / 2 + 0.5;
            %             getwndbl_scale(buf, im, x, y, amy.cw * scale, amy.ch * scale);
            getwndbl_scale(bufr, imr, x, y, cw * scale, ch * scale);
            getwndbl_scale(bufg, img, x, y, cw * scale, ch * scale);
            getwndbl_scale(bufb, imb, x, y, cw * scale, ch * scale);
            buf = [bufr(:); bufg(:); bufb(:)];
            Ty(:, row) = buf;
%             Ty(:, count) = am_project(buf(:), amy.B, amy.avg, amy.a, amy.b);
% tic

            count = count + 1;
        end
        tic
                    t = net(Ty);
                    toc
%             toc
            D(:, col) = t(2, :);
        fig(1); sc(D); drawnow;
    end
    dtproj = toc(tproj);
    fprintf('Projection: %.3f sec.\n', dtproj);
end
