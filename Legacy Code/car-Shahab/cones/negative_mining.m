am = load('am_yb_vs_bg_26x21_90_c_rgb.mat');
B = am.B .* repmat(am.a, size(am.B, 1), 1);
svm_vectors = am.svm_vectors - repmat(am.b', 1, size(am.svm_vectors, 2)) + repmat(B' * am.avg, 1, size(am.svm_vectors, 2));
svm_alphas = am.svm_alphas; svm_bias = am.svm_bias;
svm_scale = single(1.0 / (am.svm_scale * am.svm_scale));

pitch = size(B, 1) / 3;
r = B(1:pitch, :); g = B(pitch+1:pitch*2, :); b = B(pitch*2+1:end, :);
Bcuda = zeros(size(B), 'like', B);
Bcuda(1:3:end, :) = r; Bcuda(2:3:end, :) = g; Bcuda(3:3:end, :) = b;
buf = zeros(am.ch, am.cw, size(im, 3), 'single');

if 0
    %     negfn_all = [list_files('../data/negative/all/*.jpg'); ...
    %         list_files('../data/negative/all/*.png')];
    negfn_all = glob('../data/negative/**.{jpg,jpeg,png}');
    fprintf('Found %d negative images.\n', numel(negfn_all));
    negfn = {};
    warning('off')
    for i = 1:numel(negfn_all)
        info = imfinfo(negfn_all{i});
        if info.BitDepth ~= 24, continue; end
        negfn{end + 1} = negfn_all{i};
    end
    warning('on')
    % negfn = negfn_all;
    
    Nnegim = numel(negfn);
    fprintf('Of them %d are in colour.\n', Nnegim);
end

count = 1;
for im_idx = 1:numel(negfn)
    im_idx
    im = imread(negfn{im_idx});
    [h, w, ~] = size(im);
    while h >= 1024
        h = h / 2; w = w / 2;
    end
    im = imresize(im, [h w]);
    [h, w, ~] = size(im);
    
    
    imopencv = matlab2opencv(im);
    min_height_ratio = 0.020;
    max_height_ratio = 0.125;
    
    h0 = 32;
    hh = h * linspace(min_height_ratio, max_height_ratio, 5);
    ww = 0.7902 * hh;
    
    min_cc = 5;
    for i = 1:numel(ww)
%         tic
        coneness = am_project_svm_cuda(imopencv, Bcuda, svm_vectors, svm_alphas, svm_bias, svm_scale, ...
            16, 16, ww(i), hh(i));
%         toc
        t = graythresh(coneness ./ max(coneness(:)));
        bw = imbinarize(coneness, t);
        
        cc = bwconncomp(bw);
        
        for j = 1:cc.NumObjects
            % Connected component too small, skip
            if numel(cc.PixelIdxList{j}) < min_cc, continue; end
            [row, col] = ind2sub(size(bw), cc.PixelIdxList{j});
            cx = mean(col);
            cy = mean(row);
            y = cy - (hh(i) - 1) * 0.5;
            x = cx - (ww(i) - 1) * 0.5;
            getwndnn(buf, im, x, y, ww, hh);
            outfn = fullfile('../data/negative_mined', sprintf('%06d.png', count));
            imwrite(uint8(buf), outfn);
            count = count + 1;
        end
    end
end


