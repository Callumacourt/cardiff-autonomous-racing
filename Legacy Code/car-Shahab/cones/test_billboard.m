if 1
    fn = list_files('../../car_data/local/recording.261019/*.jpg');
    calib = load('../../car_data/local/recording.261019/calibration.261019.mat');
    stereoParams = calib.stereoParams;
    board = load('../../car_data/local/recording.261019/board.261019.txt', '-ascii');
    P1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0])';
    P2 = cameraMatrix(stereoParams.CameraParameters2, ...
        stereoParams.RotationOfCamera2, stereoParams.TranslationOfCamera2)';
    
    buf = zeros(24, 18, 3, 'single');
    
    net = load('cnn-experiment-cones.padded.031119/cones_cnn.mat');
    %     net = load('cnn-experiment-cones/best.mat');
    %     net = net.net;
    %     net.layers(end) = [] ;
    %     net.layers(find(cellfun(@(x)strcmp(x.type, 'dropout'), net.layers))) = [];
    
    net = vl_simplenn_move(net, 'gpu') ;
    cameraMatrix1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0]);
    cameraMatrix2 = cameraMatrix(stereoParams.CameraParameters2, eye(3), [0 0 0]);%...
end

for f = 484
    fprintf('%d / %d\n', f, numel(fn));
    %     out_fn = sprintf('out/world_cnn_pad/%05d.png', f);
    %     if isfile(out_fn), continue; end
    
    im = imread(fn{f});
    [h, w, d] = size(im);
    
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
    
    
    
    xl = [405; 288];
    xr = [177; 306];
    x3d_cam = triangulate_point([405; 288], [177; 306], P1, P2)';
    WtC = [Rl Tl; [0 0 0 1]];
    CtW = inv(WtC);
    world = rigid(CtW, x3d_cam);
%     world(3) = 13.45;
    x3d_world = [world world + [0 0 16]' world + [0 0 -19]'];
    proj_l = project_points((Rl * x3d_world + Tl)', cameraMatrix1');
    proj_r = project_points((Rr * x3d_world + Tr)', cameraMatrix2');
    
    pad = 1;
    cyl = 0.5 * (proj_l(2, 3) + proj_l(2, 2));
    cxl = mean(proj_l(1, :));
    hl = (proj_l(2, 3) - proj_l(2, 2)) * pad;
    cyr = 0.5 * (proj_r(2, 3) + proj_r(2, 2));
    cxr = mean(proj_r(1, :));
    hr = (proj_r(2, 3) - proj_r(2, 2)) * pad;
    wl = cone_width_from_height(hl);
    x = cxl - (wl - 1) * 0.5;
    y = cyl - (hl - 1) * 0.5;
    draw_bbox(imL, [x y wl hl], [0 255 0], 0.5);
%     getwndnn(buf, imL, x, y, wl, hl);
%     BUF(:, :, :, idx) = buf;
    
    wr = cone_width_from_height(hr);
    x = cxr - (wr - 1) * 0.5;
    y = cyr - (hr - 1) * 0.5;
    draw_bbox(imR, [x y wr hr], [0 255 0], 0.5);
%     getwndnn(buf, imR, x, y, wr, hr);
%     BUF(:, :, :, idx + N) = buf;
fig(1); sc([imL imR]);
end
