amy = load('am_y_vs_bg_26x21_90_rgb.mat', '-mat');
svmy_alphas = single(amy.svm.Alpha .* amy.svm.SupportVectorLabels);
svmy_vectors = single(amy.svm.SupportVectors');
svmy_bias = single(amy.svm.Bias);
% amb = load('blue_vs_bg.mat', '-mat');
% svmb_alphas = amb.svm.Alpha .* amb.svm.SupportVectorLabels;
% svmb_vectors = amb.svm.SupportVectors';
% svmb_bias = amb.svm.Bias;

opt.colour = true;


fn = list_files('../data/local/amz/*.png');

for imidx = 42%1:numel(fn)
    
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
    cw = amy.cw; ch = amy.ch;
    
    
%     s1 = 0.25;
%     s2 = 2.5;
%     n = 6;
%     a = (s2 / s1) ^ (1/(n-1));
%     scale = s1 * a.^(0:n-1);
    
    scale = [0.25 0.5 1.0 1.5 2.5];
%     scale = 1.0;
    % scale = [0.75 1.5];
    Dy = zeros(h/2, w/2, numel(scale));
    Db = zeros(h/2, w/2, numel(scale));
    buf = zeros(ch, cw, 'single');
    bufr = zeros(ch, cw, 'single');
    bufg = zeros(ch, cw, 'single');
    bufb = zeros(ch, cw, 'single');
    t1 = tic;
    
        
    % Project
    if 1
        Ty = zeros(amy.keep, h/2 * w/2, numel(scale), 'single');
%         Tb = zeros(amb.keep, h/2 * w/2, numel(scale));
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
                    
                    buf = single(buf(:));
                    
                    % TODO: same projection
                    Ty(:, count, s) = am_project(buf, amy.B, amy.avg, amy.a, amy.b);
                    %                 Tb(:, count) = am_project(buf, amb.B, amb.avg, amb.a, amb.b);
                    count = count + 1;
                    %             t = am_project(buf(:), am.B, am.avg, am.a, am.b);
                    %             tn = ((t - am.b') ./ am.a') ./ am.sd;
                    %             if any(abs(tn) > 3.5), continue; end
                    %             D(row, col, s) = kssvmpredict(t, svm_vectors, svm_alphas, svm_bias);
                    %                 Dy(row, col, s) = ...
                    %                     am_project_svm(buf(:), amy.B, amy.avg, amy.a, amy.b, amy.sd, ...
                    %                     svmy_vectors, svmy_alphas, svmy_bias);
                    %                 Db(row, col, s) = ...
                    %                     am_project_svm(buf(:), amb.B, amb.avg, amb.a, amb.b, amb.sd, ...
                    %                     svmb_vectors, svmb_alphas, svmb_bias);
                end
            end
            dtproj = toc(tproj);
            fprintf('Projection: %.3f sec.\n', dtproj);
            
        end
    end
    
    for s = 1:numel(scale)
        fprintf('Scale %.3f\n', scale(s));
        tpred = tic;
                scores = kssvmpredict(Ty(:, :, s), svmy_vectors, svmy_alphas, svmy_bias);
        %         predb = kssvmpredict(Tb, svmb_vectors, svmb_alphas, svmb_bias);
        
%         [predy1, scores] = predict(nb, Ty');
%         scores = scores(:, 2) * 2 - 1;
        %         predy1 = predy1(2, :) * 2 - 1;
        %         ignore = max(Ty) > 1.0 | min(Ty) < -0.0;
        %         predy1(ignore) = -1;
        dtpred = toc(tpred);
        fprintf('Prediction: %.3f sec.\n', dtpred);
        
        Dy(:, :, s) = reshape(scores, h/2, w/2);
        %         Db(:, :, s) = reshape(predb, h/2, w/2);
    end
    dt = toc(t1);
    fprintf('Overall: %.3f sec.\n', dt);
    
    Iy = max(Dy, [], 3);
    Iy(Iy < 0) = 0;
    Iy = rescale(Iy);
    Iy = imresize(Iy, 2);
    Iy = im2uint8(Iy);
    Jy = Iy * 2;
    
    Jb = zeros(size(Jy), class(Jy));
    %     Ib = max(Db, [], 3);
    %     Ib(Ib < 0) = 0;
    %     Ib = rescale(Ib);
    %     Ib = imresize(Ib, 2);
    %     Ib = im2uint8(Ib);
    %     Jb = Ib * 2;
    if opt.colour
        I = ([cat(3, Jy, Jy, Jb); cat(3, max(im(:, :, 1), Jy), max(im(:, :, 2), Jy), max(im(:, :, 3), Jb))]);
    else
        I = ([cat(3, Jy, Jy, Jb); cat(3, max(img, Jy), max(img, Jy), max(img, Jb))]);
    end
%    fig(1); sc(I); drawnow; 
    imwrite(I, sprintf('out/dense_rgb/%05d.png', imidx));
    
end
