% Found 1082 yellow, 927 blue, 1266 solid, 10 red cones (3285 in total) in 2817 images.

if 0 || ~exist('am', 'var')
    fprintf('Loading annotations...\n');
    [imfn, bb] = load_annotated_cones('augmented', false);
    %     detector = vision.CascadeObjectDetector('cone_detector_haar_yb_pad125_12x10_st25_far0.500_tpr0.999_nsf2.0.xml');
    %     detector = vision.CascadeObjectDetector('cone_detector_lbp_yb_pad125_12x10_st25_far0.500_tpr0.999_nsf2.0.xml');
    detector = vision.CascadeObjectDetector('cascade_16x14.xml');
    
    am = load('am_y_vs_bg_26x21_90_rgb.mat');
    %     am = load('models/am_svm/am_y_vs_bg_26x21_95_gray.mat');
    
    %     am_blue = load('blue_vs_bg.mat', '-mat');
end
detector.ScaleFactor = 1.25;
detector.MergeThreshold = 1;
detector.MinSize = [16 14];
detector.MaxSize = [16 14] * 6;

svm_alphas = single(am.svm.Alpha .* am.svm.SupportVectorLabels);
svm_vectors = single(am.svm.SupportVectors');
svm_bias = single(am.svm.Bias);


gt_col = [128 0 128];

for idx = 28%1:numel(imfn)
    
    try
        im = imread(imfn{idx});
    catch
        im = imread(replace_ext(imfn{idx}, '.jpg'));
    end
    %     fig(10); sc(im);
%     img = rgb2gray(im);
    img = im(:, :, 1);
    if am.colour
        imf = im + 0;
    else
        imf = img;
    end
    buf = zeros([am.ch, am.cw, size(imf, 3)], 'single');

    lab = bb{idx}(:, 2:end);
    
    % Detect cones
    tic
    bbox = step(detector, img);
    toc
    
    % Remove padding
    %     pad = 8;
    %     bbox(:, 1) = bbox(:, 1) + pad;
    %     bbox(:, 2) = bbox(:, 2) + pad;
    %     bbox(:, 3) = bbox(:, 3) - 2 * pad;
    %     bbox(:, 4) = bbox(:, 4) - 2 * pad;
    
    D = zeros(size(bbox, 1), 1);
    cl = []; score = [];
    yellow = zeros(size(bbox, 1), 1);
    yellow_scores = zeros(size(bbox, 1), 1);
    yellow_scores_f = zeros(size(bbox, 1), 1);
    
    % Filter detections using AM and SVM
    tic
    bboxf = bbox;
    Byellow = am.B(:, 1:am.keep);
    for i = 1:size(bbox, 1)
        b = bbox(i, :);
        yellow_scores(i) = eval_bbox(imf, buf, am, svm_vectors, svm_alphas, svm_bias, b);
        if yellow_scores(i) > -3.0
            [yellow_scores_f(i), bboxf(i, :)] = ...
                refine_bbox_grid(imf, am, svm_vectors, svm_alphas, svm_bias, b);
            if yellow_scores_f(i) > 0, yellow(i) = 1; end
        end
    end
    toc
    
    if 0
        buf = zeros([am.ch, am.cw, size(im, 3)], 'single');
        masked = find(am.mask);
        for i = 1:size(bboxf, 1)
            if ~yellow(i), continue; end
            b = round(bboxf(i, :));
            getwndbl_scale(buf, im, b(1), b(2), b(3), b(4));
            bf = buf(:); bf = bf(am.mask);
            rec = addcol(am.B * am_project(bf, am.B, am.avg, ones(size(am.a)), zeros(size(am.b))), am.avg);
            
            x = zeros(am.ch * am.cw * size(im, 3), 1, 'single');
            x(masked) = rec;
            
            res_mask = single(imresize(reshape(am.mask, am.ch, am.cw, size(im, 3)), [b(4) b(3)]));
            paste = imresize(reshape(x, am.ch, am.cw, size(im, 3)), [b(4) b(3)]);
            im(b(2):b(2)+b(4)-1, b(1):b(1)+b(3)-1, :) = res_mask .* paste + ...
                (1 - res_mask) .* single(im(b(2):b(2)+b(4)-1, b(1):b(1)+b(3)-1, :));
        end
    end
    
    %     both = yellow == 1 & blue == 1;
    %     yellow(both) = yellow_scores_f(both) >= blue_scores_f(both);
    %     blue(both) = yellow_scores_f(both) < blue_scores_f(both);
    
    % Compute bbox centroids
    %     labc = bbox_centroids(lab);
    bboxc = bbox_centroids(bbox);
    bboxfc = bbox_centroids(bboxf);
    
    % Plot bboxes
    im = draw_bbox(im, bbox(yellow == 0, :), [255 255 255], 0.25);
    
    %     im = draw_bbox(im, bbox(yellow == 1, :), [192 0 0], 0.75);
    %     im = draw_bbox(im, bbox(blue == 1, :), [0 0 192], 0.75);
    
    im = draw_bbox(im, bboxf(yellow == 1, :), [255 255 0], 1);
    %     im = draw_bbox(im, bboxf(blue == 1, :), [64 64 255], 1);
    % im = draw_bbox(im, bboxf, [255 64 0], 1);
    %     im = draw_bbox(im, lab, gt_col, 0.5);
    
    % Plot bbox numbers
    for i = 1:size(bbox, 1)
        %     im = insertText(im, bbox(i, 1:2) + [bbox(i, 3) 0.5 * bbox(i, 4)], ...
        %         num2str(i), ...
        %         'TextColor', [255 255 128], 'BoxColor', [255 128 128], ...
        %         'AnchorPoint', 'LeftCenter', 'BoxOpacity', 0.25, ...
        %         'Font', 'VL-Gothic-Regular', 'FontSize', 12);
        
        if yellow(i) && 0
            c = [255 255 0];
            im = insertText(im, bbox(i, 1:2) + [0.5 * bbox(i, 3) 0.0 * bbox(i, 4)], ...
                sprintf('%.2f', yellow_scores(i)), ...
                'TextColor', c, 'BoxColor', [0 0 0], ...
                'AnchorPoint', 'CenterBottom', 'BoxOpacity', 0.25, ...
                'Font', 'RobotoCondensed-Regular', 'FontSize', 10);
            im = insertText(im, bbox(i, 1:2) + [0.5 * bbox(i, 3) 1.0 * bbox(i, 4)], ...
                sprintf('%.2f', yellow_scores_f(i)), ...
                'TextColor', c, 'BoxColor', [0 0 0], ...
                'AnchorPoint', 'CenterTop', 'BoxOpacity', 0.25, ...
                'Font', 'RobotoCondensed-Regular', 'FontSize', 10);
        end
    end
    % for i = 1:size(lab, 1)
    %     im = insertText(im, lab(i, 1:2) + [0 0.5 * lab(i, 4)], ...
    %         num2str(i), ...
    %         'TextColor', [255 255 128], 'BoxColor', [128 255 128], ...
    %         'AnchorPoint', 'RightCenter', 'BoxOpacity', 0.25, ...
    %         'Font', 'VL-Gothic-Regular', 'FontSize', 12);
    % end
    
    % Plot centroids
    %     im = draw_cross(im, labc(1, :)', labc(2, :)', gt_col, 1);
    %     im = draw_cross(im, bboxc(1, yellow == 1)', bboxc(2, yellow == 1)', [192 192 0], 0.75);
    %     im = draw_cross(im, bboxc(1, blue == 1)', bboxc(2, blue == 1)', [0 0 192], 0.75);
    
    %     im = draw_cross(im, bboxfc(1, yellow == 1)', bboxfc(2, yellow == 1)', [255 255 0], 1);
    %     im = draw_cross(im, bboxfc(1, blue == 1)', bboxfc(2, blue == 1)', [0 0 255], 1);
    fig(1); sc(im);
    drawnow;
    imwrite(im, sprintf('out/svm_test_pad125/%05d.png', idx));
end
