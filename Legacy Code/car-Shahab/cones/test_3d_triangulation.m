if 1
    %     net = load('good_cnns/cnn-experiment-cones-np-23x17-8-8-8-16-4classes/cones_cnn.mat');
%     net = load('cnn-experiment-cones-np-23x17-6-4-6-6-4classes-do00-bn/cones_cnn.mat');
    net = load('cnn-experiment-cones-np-23x17-8-6-6-8-4classes-do00-bn/best.mat');
    net = net.net;
    net.layers(end) = [] ;
    net = cnn_remove_bnorm(net);
    net.layers(find(cellfun(@(x)strcmp(x.type, 'dropout'), net.layers))) = []; %#ok<FNDSB>
    
    net = vl_simplenn_move(net, 'gpu');
    
%         fn = list_files('~/research/car_data/test_days/2019-12-11/recording0_flipped/*.jpg');
%         calib = load('../../car_data/test_days/2019-12-11/recording0_calib_flipped/stereoParams.mat');
%         GtoC = load('~/research/car_data/test_days/2019-12-11/recording0_calib_flipped/GtoC.mat'); GtoC = GtoC.GtoC;
    
    fn = list_files('~/research/car_data/cones/fsuk19/track1/*.jpg');
    calib = load('../../car_data/cones/fsuk19_calibration/calibration_track1_side1_before/stereoParams.mat');
    GtoC = load('../../car_data/cones/fsuk19_calibration/calibration_track1_side1_before/GtoC.mat');
    GtoC = GtoC.GtoC;
    
    stereoParams = calib.stereoParams;
    CtoG = inv(GtoC);
    P1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0])';
    P2 = cameraMatrix(stereoParams.CameraParameters2, ...
        stereoParams.RotationOfCamera2, stereoParams.TranslationOfCamera2)';
%     cameraMatrix1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0]);
%     cameraMatrix2 = cameraMatrix(stereoParams.CameraParameters2, eye(3), [0 0 0]);%...
    I1 = stereoParams.CameraParameters1.IntrinsicMatrix;
    I2 = stereoParams.CameraParameters2.IntrinsicMatrix;
    
%     P1_ = vision.internal.constructCameraMatrix(eye(3), zeros(1, 3), I1)';
%     P2_ = vision.internal.constructCameraMatrix(stereoParams.RotationOfCamera2, stereoParams.TranslationOfCamera2, I2)';
    
    cameraMatrix1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0]);
    cameraMatrix2 = cameraMatrix(stereoParams.CameraParameters2, eye(3), [0 0 0]);%...
    pose = inv(I2') * P2;
    % Compute the essential matrix
    relR = pose(:, 1:3)';
    trans = -relR * pose(:, 4); trans = trans ./ vnorm(trans);
    essential = [0 -trans(3) trans(2); trans(3) 0 -trans(1); -trans(2) trans(1) 0] * relR;
end
scale = 1; % Initial scale
scales = 1.5  .^ -(0:4);
cd_hard_threshold = 0.95;
cd_soft_threshold = 0.50;
dev = gpuDevice();

info = imfinfo(fn{1});
w = info.Width / 2; h = info.Height;

frame_count = 1000;
for frame = 1:numel(fn)
    fprintf('%d\n', frame);
    im = imread(fn{frame});
    
    % Split the combined image into left and right
    [imL_distorted, imR_distorted] = split_stereo_image(im);
    
    % Undo the camera distortion
    imL = undistortImage(imL_distorted, stereoParams.CameraParameters1);
    imR = undistortImage(imR_distorted, stereoParams.CameraParameters2);
    %     imLg = rgb2gray(im2double(imL));
    %     imRg = rgb2gray(im2double(imR));
    img = rgb2gray(im2double(im));
    [h, w, d] = size(imL);
    
    % Detect cones
    tic
    Cl = detect_cnn_multiscale(imL, net, scale, scales);
    Cr = detect_cnn_multiscale(imR, net, scale, scales);
    wait(dev); toc
    
    % Detect and analyse connected components
    Cl = gather(Cl); Cr = gather(Cr);
    [Cl_max, Cl_label] = max(Cl, [], 3);
    [Cr_max, Cr_label] = max(Cr, [], 3);
    
    Cl_soft = Cl_max; Cl_soft(Cl_soft < cd_soft_threshold) = 0.0;
    Cr_soft = Cr_max; Cr_soft(Cr_soft < cd_soft_threshold) = 0.0;
    
    %     Cl_hard = Cl > cd_hard_threshold;
    %     Cr_hard = Cr > cd_hard_threshold;
    
    ccl = bwconncomp(Cl_soft);
    ccr = bwconncomp(Cr_soft);
%     ccl = ccmerge(ccl);
%     ccr = ccmerge(ccr);
    ctrl = cccentroids(ccl, Cl_soft, cd_hard_threshold);
    ctrr = cccentroids(ccr, Cr_soft, cd_hard_threshold);
    
    % Assign cone labels to connected components
    labl = zeros(1, size(ctrl, 2));
    for i = 1:numel(labl)
        lab = Cl_label(ccl.PixelIdxList{i});
        labl(i) = mode(lab);
    end
    
    labr = zeros(1, size(ctrr, 2));
    for i = 1:numel(labr)
        lab = Cr_label(ccr.PixelIdxList{i});
        labr(i) = mode(lab);
    end
    
    % Filter those below the hard threshold
    labl(ctrl(4, :) == 0) = [];
    labr(ctrr(4, :) == 0) = [];
    ctrl(:, ctrl(4, :) == 0) = [];
    ctrr(:, ctrr(4, :) == 0) = [];
    
    
    G = zeros(size(ctrl, 2), size(ctrr, 2));
    W = zeros(size(ctrl, 2), size(ctrr, 2), 3);
    Wg = zeros(size(ctrl, 2), size(ctrr, 2), 3);
    for i = 1:size(ctrl, 2)
        for j = 1:size(ctrr, 2)
            % TODO: Triangulate blobs
            [p3d, err] = triangulate_point(ctrl(1:2, i), ctrr(1:2, j), P1, P2);
%             [p3d0, err0] = triangulate_point_nonlin(ctrl(1:2, i), ctrr(1:2, j), P1, P2, w, h);
%             [p3d, err] = triangulate_point_new(ctrl(1:2, i), ctrr(1:2, j), P1, P2, I1, I2, pose, essential);
            %             [p3d1, err1] = triangulate_point_nonlin(ctrl(1:2, i), ctrr(1:2, j), P1, P2, w, h);
            
            W(i, j, :) = p3d;
            ground = rigid(CtoG, p3d);
            Wg(i, j, :) = ground;
            err = max(err);
            if err > 5 || p3d(3) < 0 || labl(i) ~= labr(j) % || ground(3) < -500 || ground(3) > 500
                G(i, j) = 100;
            else
%                 [max(err0) max(err)]
%                 vnorm(p3d - p3d0')
                G(i, j) = err + abs(ground(3)) * 0.05;%-exp(-err);
            end
        end
    end
    [A, cost] = hungarian(G);
    [row, col] = find(A);
    edges = [row col]';
    edge_cost = G(A == 1);
    X = reshape(W(repmat(A == 1, 1, 1, 3)), [], 3)';
    X(:, edge_cost >= 10000) = [];
    edges(:, edge_cost >= 10000) = [];
    edge_cost(edge_cost >= 10000) = [];
    
    
    imd = img * 1;
    text_opt = {'FontSize', 14, ...
        'TextColor', [0.9961 0.5020 0.0980], 'BoxColor', 'black', ...
        'AnchorPoint', 'CenterBottom', ...
        'BoxOpacity', 0.3, 'Font', 'RobotoCondensed-Medium'};
    
    cone_colours = [0.75 0.75 0.0; 0.0 0.0 1.0; 1.0 0.0 0.0];
    for l = 1:3
        imd = insertShape(imd, 'FilledCircle', ...
            ctrl(1:3, labl == l)', 'Color', cone_colours(l, :));
        imd = insertShape(imd, 'FilledCircle', ...
            (ctrr(1:3, labr == l) + [w; 0; 0])', 'Color', cone_colours(l, :));
    end
    
    if ~isempty(ctrl)
        imd = insertText(imd, ...
            [ctrl(1, :); ctrl(2, :) + 4]', 1:size(ctrl, 2), ...
            'TextColor', 'red', 'BoxColor', 'black', ...
            'AnchorPoint', 'CenterTop', 'BoxOpacity', 0.3, 'Font', 'RobotoCondensed-Medium');
    end
    if ~isempty(ctrr)
        imd = insertText(imd, ...
            [ctrr(1, :) + w; ctrr(2, :) + 4]', 1:size(ctrr, 2), ...
            'TextColor', 'red', 'BoxColor', 'black', ...
            'AnchorPoint', 'CenterTop', 'BoxOpacity', 0.3, 'Font', 'RobotoCondensed-Medium');
    end
    if ~isempty(edges)
        for i = 1:size(edges, 2)
            imd = insertText(imd, [ctrl(1, edges(1, i)), ctrl(2, edges(1, i)) - 8], ...
                sprintf('%02d', i), text_opt{:});
            imd = insertText(imd, [ctrr(1, edges(2, i)) + w, ctrr(2, edges(2, i)) - 8], ...
                sprintf('%02d', i), text_opt{:});
        end
        imd = insertShape(imd, 'Line', ...
            [ctrl(1:2, edges(1, :)); ctrr(1:2, edges(2, :)) + [w; 0]]', ...
            'LineWidth', 2, 'Color', [0.9961 0.5020 0.0980]);
    end
    fig(1); sc(imd);
    
    if size(X, 2) > 3
        % Estimate ground
        WO = mean(X, 2);
        Xn = bsxfun(@minus, X, WO);
        [V, ~, ~] = svd(Xn);
        OZ = V(:, 3);
        % Project camera origin onto the ground plane
        dist = dot(OZ, -WO); % Height of camera over the ground
        GO = -dist * OZ; % Origin of the ground coordinate system (in camera coordinates)
        
        F = -WO + [0; 0; 1]; % Forward vector
        GY = [0; 0; 1] - dot(OZ, F) * OZ;
        
        % Ground coordinate system unit vectors (in camera coordinates)
        GOY = GY - GO; GOY = GOY ./ vnorm(GOY);
        GOZ = -GO; GOZ = GOZ ./ vnorm(GOZ);
        GOX = cross(GOY, GOZ);
        
        GtoC = [GOX(:) GOY(:) GOZ(:) GO(:); 0 0 0 1];
        CtoG = inv(GtoC);
        rad2deg(rodrigues(GtoC(1:3, 1:3)))'
    end
    fig(2); clf;
    hold on
    if ~isempty(edges)
        for i = 1:size(edges, 2)
            %             [p3d, err] = triangulate_point_nonlin(ctrl(1:2, edges(1, i)), ctrr(1:2, edges(2, i)), P1, P2, h, w);
            p3d = X(:, i);
            p3dg = rigid(CtoG, p3d);
%             fprintf('%4.2f %4.2f %4.2f\n', p3dg(1), p3dg(2), p3dg(3));
            fprintf('%4.2f %4.2f %4.2f\n', p3d(1), p3d(2), p3d(3));
            plot(p3dg(1), p3dg(2), '.', ...
                'MarkerFaceColor', cone_colours(labl(edges(1, i)), :), ...
                'MarkerEdgeColor', cone_colours(labl(edges(1, i)), :), ...
                'MarkerSize', 64);
        end
    end
    axis equal
    xlim([-715 715]);
    ylim([0 2000]);
    grid minor
    hold off
    drawnow;
    if 0
    export_fig('temp.png');
    plan = im2double(imread('temp.png'));
    if size(plan, 3) == 1
        plan = cat(3, plan, plan, plan);
    end
    plan = imresize(plan, size(imd, 1) / size(plan, 1));
%     imwrite([imd plan], sprintf('out/triang_fsuk19_g/%06d.png', frame));
    frame_count = frame_count + 1;
    end
    
    Xg = rigid(CtoG, X);
    Xg = [Xg(1:2, :); labl(edges(1, :))];
%     save(sprintf('out/points/%06d.mat', frame), 'Xg');
end
