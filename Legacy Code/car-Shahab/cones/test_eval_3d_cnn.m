if 1
    fn = list_files('../../car_data/local/recording.261019/*.jpg');
    calib = load('../../car_data/local/recording.261019/calibration.261019.mat');
    stereoParams = calib.stereoParams;
    board = load('../../car_data/local/recording.261019/board.261019.txt', '-ascii');
    P1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0])';
    P2 = cameraMatrix(stereoParams.CameraParameters2, ...
        stereoParams.RotationOfCamera2, stereoParams.TranslationOfCamera2)';
    
    
    
    
    net = load('cnn-experiment-cones.shifted.padded/cones_cnn.mat');
    channels = size(net.layers{1}.weights{1}, 3);
    buf = zeros(24, 18, 3, 'single');
    %     net = load('cnn-experiment-cones/best.mat');
    %     net = net.net;
    %     net.layers(end) = [] ;
    %     net.layers(find(cellfun(@(x)strcmp(x.type, 'dropout'), net.layers))) = [];
    
    net = vl_simplenn_move(net, 'gpu') ;
    cameraMatrix1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0]);
    cameraMatrix2 = cameraMatrix(stereoParams.CameraParameters2, eye(3), [0 0 0]);%...
end

x3d = [119.7213  116.5625  991.6433]'; % Frame 100
x3d_world = [200.6644 203.8978 13.4495]';
x3d_world = [274.6274 102.9200 11.1130]'; % Frame 186

N = numel(fn);
x_range = 580;
y_range = 800;
step = 4;
[xx, yy] = meshgrid(x_range:-step:0, 0:step:y_range);
Cl = zeros(size(xx));
Cr = zeros(size(xx));
X = [xx(:) yy(:) zeros(numel(xx), 1)]';
% X = [274.6274 102.9200 0]';
for f = 6:1:numel(fn)
    fprintf('%d / %d\n', f, numel(fn));
    out_fn = sprintf('out/world_cnn_pad_gray/%05d.png', f);
    if isfile(out_fn), continue; end
    
    im = imread(fn{f});
    [h, w, d] = size(im);
    Cl = zeros(size(xx, 1), size(xx, 2), 3);
    Cr = zeros(size(xx, 1), size(xx, 2), 3);
    
    % Split the combined image into left and right
    imL = im(:, 1:w / 2, :);
    imR = im(:, w / 2 + 1:end, :);
    % Undo the camera distortion
    imL = undistortImage(imL, stereoParams.CameraParameters1);
    imR = undistortImage(imR, stereoParams.CameraParameters2);
    
    t = board(f, :);
    rotl = rodrigues(t(2:4)'); transl = t(5:7)';
    rotr = rodrigues(t(9:11)'); transr = t(12:14)';
    [Rl, Tl, Rr, Tr] = world_to_stereo_transform(stereoParams, rotl, transl, t(1), rotr, transr, t(8));
    if isempty(Rl) || isempty(Rr), continue, end
    if 1
        N = size(Cl, 1) * size(Cl, 2);
        z_range = -5:2.5:0;
        BUF = zeros(size(buf, 1), size(buf, 2), channels, N * 2 * numel(z_range), 'single');
        idx = 0;
        tic
        visL = zeros(size(xx, 1), size(xx, 2));
        visR = zeros(size(xx, 1), size(xx, 2));
        
        for col = 1:size(Cl, 2)
            for row = 1:size(Cl, 1)
                idx = idx + 1;
                for z_idx = 1:numel(z_range)
                    world = [xx(row, col); yy(row, col); 13.45 + z_range(z_idx)];
                    x3d_world = [world world + [0 0 16]' world + [0 0 -19]'];
                    proj_l = project_points((Rl * x3d_world + Tl)', cameraMatrix1');
                    proj_r = project_points((Rr * x3d_world + Tr)', cameraMatrix2');
                    
                    if ~(proj_l(1, 1) < 0 || proj_l(1, 1) > size(imL, 2) || proj_l(2, 1) < 0 || proj_l(2, 1) > size(imL, 1))
                        visL(row, col) = 1;
                    end
                    
                    if ~(proj_r(1, 1) < 0 || proj_r(1, 1) > size(imR, 2) || proj_r(2, 1) < 0 || proj_r(2, 1) > size(imR, 1))
                        visR(row, col) = 1;
                    end
                    
                    %                 if proj_l(1, 1) < 0 || proj_l(1, 1) > size(imL, 2) || proj_l(2, 1) < 0 || proj_l(2, 1) > size(imL, 1) || ...
                    %                         proj_r(1, 1) < 0 || proj_r(1, 1) > size(imR, 2) || proj_r(2, 1) < 0 || proj_r(2, 1) > size(imR, 1)
                    %                     continue
                    %                 end
                    
                    
                    if visL(row, col) || visR(row, col)
                        pad = 1.25;
                        cyl = 0.5 * (proj_l(2, 3) + proj_l(2, 2));
                        cxl = mean(proj_l(1, :));
                        hl = (proj_l(2, 3) - proj_l(2, 2)) * pad;
                        cyr = 0.5 * (proj_r(2, 3) + proj_r(2, 2));
                        cxr = mean(proj_r(1, :));
                        hr = (proj_r(2, 3) - proj_r(2, 2)) * pad;
                        wl = cone_width_from_height(hl);
                        x = cxl - (wl - 1) * 0.5;
                        y = cyl - (hl - 1) * 0.5;
                        getwndnn(buf, imL, x, y, wl, hl);
                        if channels == 3
                            BUF(:, :, :, idx + (z_idx - 1) * 2 * N) = buf;
                        else
                            BUF(:, :, :, idx + (z_idx - 1) * 2 * N) = buf(:, :, 1);
                        end
                        
                        wr = cone_width_from_height(hr);
                        x = cxr - (wr - 1) * 0.5;
                        y = cyr - (hr - 1) * 0.5;
                        getwndnn(buf, imR, x, y, wr, hr);
                        if channels == 3
                            BUF(:, :, :, idx + (z_idx - 1) * 2 * N + N) = buf;
                        else
                            BUF(:, :, :, idx + (z_idx - 1) * 2 * N + N) = buf(:, :, 1);
                        end
                    end
                end
            end
        end
        toc
    end
    
    
    tic
    batch_size = 32768;
    first = 1;
    score = zeros(3, size(BUF, 4));
    for batch = 1:ceil(size(BUF, 4) / batch_size)
        last = min(size(BUF, 4), first + batch_size - 1);
        buf_gpu = gpuArray(BUF(:, :, :, first:last));
        res = vl_simplenn(net, buf_gpu, [], [], 'ConserveMemory', false);
        score(:, first:last) = softmax(squeeze(gather(res(end).x)));
        first = first + batch_size;
    end
    toc
    
    score_l = zeros(3, N);
    score_r = zeros(3, N);
    for z_idx = 1:numel(z_range)
        score_l = max(score_l, score(:, 1 + (z_idx - 1) * 2 * N:N + (z_idx - 1) * 2 * N));
        score_r = max(score_r, score(:, 1 + (z_idx - 1) * 2 * N + N:N + (z_idx - 1) * 2 * N + N));
    end
    
    %     score_r = score(:, size(score, 2)/2+1:end);
    
    Cl = cat(3, reshape(score_l(1, :), size(Cl, 1), size(Cl, 2)), ...
        reshape(score_l(2, :), size(Cl, 1), size(Cl, 2)), ...
        reshape(score_l(3, :), size(Cl, 1), size(Cl, 2)));
    Cr = cat(3, reshape(score_r(1, :), size(Cr, 1), size(Cr, 2)), ...
        reshape(score_r(2, :), size(Cr, 1), size(Cr, 2)), ...
        reshape(score_r(3, :), size(Cr, 1), size(Cr, 2)));
    fig(2); sc([sc(Cl) sc(Cr)]);
    
    Clfg = Cl(:, :, 3) < Cl(:, :, 1) + Cl(:, :, 2);
    Crfg = Cr(:, :, 3) < Cr(:, :, 1) + Cr(:, :, 2);
    
    Clyb = Cl(:, :, 1:2); Clyb = Clyb ./ sum(Clyb, 3);
    Clyb = Clyb .* cat(3, Clfg, Clfg);
    Cryb = Cr(:, :, 1:2); Cryb = Cryb ./ sum(Cryb, 3);
    Cryb = Cryb .* cat(3, Crfg, Crfg);
    
    left_only = repmat(visL & ~visR, [1 1 2]);
    right_only = repmat(~visL & visR, [1 1 2]);
    
    C = max(0, Clyb) .* max(0, Cryb);
    %     C(left_only) = Clyb(left_only);
    %     C(right_only) = Cryb(right_only);
    
    
    B = sum(C, 3) > 0;
    cc = bwconncomp(B);
    ctr = zeros(2, cc.NumObjects);
    ctr3d = zeros(3, cc.NumObjects);
    cone_colours = zeros(1, cc.NumObjects);
    cy = C(:, :, 1); cb = C(:, :, 2);
    for i = 1:size(ctr, 2)
        idx = cc.PixelIdxList{i};
        ccx = xx(idx);
        ccy = yy(idx);
        [r, c] = ind2sub(size(B), idx);
        ctr3d(:, i) = [mean(ccx); mean(ccy); 0];
        ctr(:, i) = [mean(c); mean(r)];
        ny = sum(cy(idx));
        nb = sum(cb(idx));
        if ny > nb
            cone_colours(i) = 0;
        else
            cone_colours(i) = 1;
        end
    end
    
    
    
    
    Cyl = cat(3, 1.0 * Clyb(:, :, 1), 1.0 * Clyb(:, :, 1), 0.0 * Clyb(:, :, 1));
    Cbl = cat(3, 0.3 * Clyb(:, :, 2), 0.3 * Clyb(:, :, 2), 1.0 * Clyb(:, :, 2));
    Cyr = cat(3, 1.0 * Cryb(:, :, 1), 1.0 * Cryb(:, :, 1), 0.0 * Cryb(:, :, 1));
    Cbr = cat(3, 0.3 * Cryb(:, :, 2), 0.3 * Cryb(:, :, 2), 1.0 * Cryb(:, :, 2));
    Cy = cat(3, 1.0 * C(:, :, 1), 1.0 * C(:, :, 1), 0.0 * C(:, :, 1));
    Cb = cat(3, 0.3 * C(:, :, 2), 0.3 * C(:, :, 2), 1.0 * C(:, :, 2));
    
    if size(ctr, 2) > 3
        tri = delaunay(ctr');
        Cyb = uint8(sc(Cy + Cb) * 255);
        Cyb = imtriplot(Cyb, tri, ctr, [128 128 128], 0.2);
        vert_colours = cone_colours(tri);
        remove = (sum(vert_colours, 2) == 0 | sum(vert_colours, 2) == 3);
        tri(remove, :) = [];
        edges = tri2edges(tri);
        if ~isempty(edges)
            %     Cyb = imtriplot(Cyb, tri, ctr, [128 128 128], 1.0);
            edge_colours = cone_colours(edges);
            edges_y = edges(:, all(edge_colours == 0));
            edges_b = edges(:, all(edge_colours == 1));
            draw_line(Cyb, ctr(:, edges_y(1, :)), ctr(:, edges_y(2, :)), [255 255 0], 0.75);
            draw_line(Cyb, ctr(:, edges_b(1, :)), ctr(:, edges_b(2, :)), [64 64 255], 0.75);
            
            [proj_l_ctr, proj_ctr_r] = world_to_stereo(ctr3d, stereoParams, cameraMatrix1, cameraMatrix2, rotl, transl, t(1), rotr, transr, t(8));
            draw_line(imL, proj_l_ctr(:, edges_y(1, :)), proj_l_ctr(:, edges_y(2, :)), [255 255 0], 0.75);
            draw_line(imL, proj_l_ctr(:, edges_b(1, :)), proj_l_ctr(:, edges_b(2, :)), [64 64 255], 0.75);
            draw_line(imR, proj_ctr_r(:, edges_y(1, :)), proj_ctr_r(:, edges_y(2, :)), [255 255 0], 0.75);
            draw_line(imR, proj_ctr_r(:, edges_b(1, :)), proj_ctr_r(:, edges_b(2, :)), [64 64 255], 0.75);
        end
    end
    Xy = X; Xy(3, :) = reshape(max(0, C(:, :, 1)), 1, []) * 50;
    Xb = X; Xb(3, :) = reshape(max(0, C(:, :, 2)), 1, []) * 50;
    [proj_l_b, proj_r_b] = world_to_stereo(X, stereoParams, cameraMatrix1, cameraMatrix2, rotl, transl, t(1), rotr, transr, t(8));
    [proj_l_ty, proj_r_ty] = world_to_stereo(Xy, stereoParams, cameraMatrix1, cameraMatrix2, rotl, transl, t(1), rotr, transr, t(8));
    [proj_l_tb, proj_r_tb] = world_to_stereo(Xb, stereoParams, cameraMatrix1, cameraMatrix2, rotl, transl, t(1), rotr, transr, t(8));
    for i = 1:size(proj_l_ty, 2)
        if vnorm(proj_l_b(:, i) - proj_l_ty(:, i)) > 0.1
            draw_line(imL, proj_l_b(:, i), proj_l_ty(:, i), [255 255 0], 0.5);
            draw_line(imR, proj_r_b(:, i), proj_r_ty(:, i), [255 255 0], 0.5);
        end
        if vnorm(proj_l_b(:, i) - proj_l_tb(:, i)) > 0.1
            draw_line(imL, proj_l_b(:, i), proj_l_tb(:, i), [64 64 255], 0.5);
            draw_line(imR, proj_r_b(:, i), proj_r_tb(:, i), [64 64 255], 0.5);
        end
    end
    
    grid_colour = [96 255 0];
    for x = 0:100:x_range
        [pl1, pr1] = world_to_stereo([x; 0; 0], stereoParams, cameraMatrix1, cameraMatrix2, rotl, transl, t(1), rotr, transr, t(8));
        [pl2, pr2] = world_to_stereo([x; y_range; 0], stereoParams, cameraMatrix1, cameraMatrix2, rotl, transl, t(1), rotr, transr, t(8));
        draw_line(imL, pl1, pl2, grid_colour, 0.2);
        draw_line(imR, pr1, pr2, grid_colour, 0.2);
    end
    for y = 0:100:y_range
        [pl1, pr1] = world_to_stereo([0; y; 0], stereoParams, cameraMatrix1, cameraMatrix2, rotl, transl, t(1), rotr, transr, t(8));
        [pl2, pr2] = world_to_stereo([x_range; y; 0], stereoParams, cameraMatrix1, cameraMatrix2, rotl, transl, t(1), rotr, transr, t(8));
        draw_line(imL, pl1, pl2, grid_colour, 0.2);
        draw_line(imR, pr1, pr2, grid_colour, 0.2);
    end
    
    im_c = [sc(Cyl + Cbl) ones(size(Cl, 1), 4, 3) sc(Cyr + Cbr) ones(size(Cl, 1), 4, 3) sc(Cyb)];
    im_out = [double([imL imR]) ./ 255; imresize(im_c, 2 * size(imL, 2) / size(im_c, 2), 'bilinear')];
    fig(1); sc(im_out);
    imwrite(im_out, out_fn);
    drawnow;
    
    %     save(replace_ext(out_fn, 'mat'), 'C');
    
end
% TODO:
% Project the cone bbox less naively, like a billboard
% 1244
% [point3d, reprojectionErrors] = triangulate_point([380; 192], [212; 209], P1, P2)
