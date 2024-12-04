if 1
    fn = list_files('../data/recording.261019/*.jpg');
    calib = load('../data/recording.261019/calibration.261019.mat');
    stereoParams = calib.stereoParams;
    board = load('../data/recording.261019/board.261019.txt', '-ascii');
    P1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0])';
    P2 = cameraMatrix(stereoParams.CameraParameters2, ...
        stereoParams.RotationOfCamera2, stereoParams.TranslationOfCamera2)';
    am = load('am_yb_vs_bg_26x21_90_c_rgb.mat');
    
    buf = zeros(am.ch, am.cw, 3, 'single');
    
    B = am.B .* repmat(am.a, size(am.B, 1), 1);
    svm_vectors = am.svm_vectors - repmat(am.b', 1, size(am.svm_vectors, 2)) + repmat(B' * am.avg, 1, size(am.svm_vectors, 2));
    svm_alphas = am.svm_alphas;
    svm_bias = am.svm_bias;
    svm_scale = single(1.0 / (am.svm_scale * am.svm_scale));
    
end

x3d = [119.7213  116.5625  991.6433]'; % Frame 100
x3d_world = [200.6644 203.8978 13.4495]';
x3d_world = [274.6274 102.9200 11.1130]'; % Frame 186

N = numel(fn);
[xx, yy] = meshgrid(0:5:500, 0:5:700);
Cl = zeros(size(xx));
Cr = zeros(size(xx));
X = [xx(:) yy(:) zeros(numel(xx), 1)]';
% X = [274.6274 102.9200 0]';
for f = 193:numel(fn)
    im = imread(fn{f});
    [h, w, d] = size(im);
    Cl = zeros(size(xx));
    Cr = zeros(size(xx));
    
    % Split the combined image into left and right
    imL = im(:, 1:w / 2, :);
    imR = im(:, w / 2 + 1:end, :);
    % Undo the camera distortion
    imL = undistortImage(imL, stereoParams.CameraParameters1);
    imR = undistortImage(imR, stereoParams.CameraParameters2);
    
    t = board(f, :);
    rotl = rodrigues(t(2:4)'); transl = t(5:7)';
    rotr = rodrigues(t(9:11)'); transr = t(12:14)';
    
    
    for row = 1:size(Cl, 1)
        for col = 1:size(Cl, 2)
            for z = -2.5:2.5:5
                x3d_world = [xx(row, col); yy(row, col); 13.45 + z];
                x3d_world = [x3d_world x3d_world + [0 0 16]' x3d_world + [0 0 -19]'];
                [proj_l, proj_r] = world_to_stereo(x3d_world, stereoParams, rotl, transl, t(1), rotr, transr, t(8));
                if proj_l(1, 1) < 0 || proj_l(1, 1) > size(imL, 2) || proj_l(2, 1) < 0 || proj_l(2, 1) > size(imL, 1) || ...
                        proj_r(1, 1) < 0 || proj_r(1, 1) > size(imR, 2) || proj_r(2, 1) < 0 || proj_r(2, 1) > size(imR, 1)
                    continue
                end
                
                cyl = 0.5 * (proj_l(2, 3) + proj_l(2, 2));
                cxl = mean(proj_l(1, :));
                hl = proj_l(2, 3) - proj_l(2, 2);
                cyr = 0.5 * (proj_r(2, 3) + proj_r(2, 2));
                cxr = mean(proj_r(1, :));
                hr = proj_r(2, 3) - proj_r(2, 2);
                %             bbox = [cx - 0.5 * w, cy - 0.5 * h, w, h];
                
                Cl(row, col) = max(Cl(row, col), eval_bbox_multiscale(cxl, cyl, hl, imL, buf, B, svm_vectors, svm_alphas, svm_bias, svm_scale));
                if abs(Cl(row, col)) < 0.0000001, continue; end
                Cr(row, col) = max(Cr(row, col), eval_bbox_multiscale(cxr, cyr, hr, imR, buf, B, svm_vectors, svm_alphas, svm_bias, svm_scale));
                
            end
            %             imL = draw_bbox(imL, bbox, [0 128 0], 0.5);
            %             fig(1); sc(imL);
            %             if ~isempty(proj_l)
            %                 hold on
            %                 plot(proj_l(1, :), proj_l(2, :), 'g.', 'MarkerSize', 8);
            %                 hold off
            %             end
            %
            %
            %             fig(2); sc(imR);
            %             if ~isempty(proj_r)
            %                 hold on
            %                 plot(proj_r(1, :), proj_r(2, :), 'g.', 'MarkerSize', 8);
            %                 hold off
            %             end
            %
            %             drawnow;
        end
        if mod(row, 10) == 0
            fig(3); sc([sc(Cl) sc(Cr)]);
            drawnow;
        end
    end
    fig(3); sc([sc(Cl) sc(Cr)]);
    
    C = max(0, Cl) .* max(0, Cr);
    Xl = X; Xl(3, :) = reshape(max(0, C), 1, []) * 10;
    [proj_l_b, proj_r_b] = world_to_stereo(X, stereoParams, rotl, transl, t(1), rotr, transr, t(8));
    [proj_l_t, proj_r_t] = world_to_stereo(Xl, stereoParams, rotl, transl, t(1), rotr, transr, t(8));
    for i = 1:size(proj_l_t, 2)
        draw_line(imL, proj_l_b(:, i), proj_l_t(:, i), [0 255 0], 0.5);
        draw_line(imR, proj_r_b(:, i), proj_r_t(:, i), [0 255 0], 0.5);
    end
    
    im_c = [sc(Cl, jet) zeros(size(Cl, 1), 16, 3) sc(Cr, jet) zeros(size(Cl, 1), 16, 3) sc(C, jet)];
    im_out = [double([imL imR]) ./ 255; imresize(im_c, 2 * size(imL, 2) / size(im_c, 2), 'bilinear')];
    fig(1); sc(im_out);
    imwrite(im_out, sprintf('out/world/%05d.png', f));
    drawnow;
    
    
end

% [point3d, reprojectionErrors] = triangulate_point([380; 192], [212; 209], P1, P2)
