det_fn = 'train_16x14/cascade.xml';
fprintf('Loading template...\n');
load('../data/recording.261019/calibration.261019.mat');
experiment = 'stereo3';
CONE_HEIGHT_MAX = 90;
CONE_HEIGHT_MIN = 30;
MAX_REPROJ_ERR = 5.0;
MAX_Z = 2000;
BORDER = 6;
RMS_MIN = 5.0;

OUT_VID = ['out/' experiment '.avi'];

% vid = VideoWriter(OUT_VID, 'Motion JPEG AVI');
% vid.Quality = 95;

detector = vision.CascadeObjectDetector(det_fn, ...
    'MinSize', [16 14], 'MaxSize', [16 14] * 5, ...
    'MergeThreshold', 1, 'ScaleFactor', 1.1);
figure(1); clf;
% figure(2); clf;
fn = list_files('../data/recording.261019/*.jpg');

cameraMatrix1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0]);
cameraMatrix2 = cameraMatrix(stereoParams.CameraParameters2, ...
    stereoParams.RotationOfCamera2, stereoParams.TranslationOfCamera2);

D = []; H = [];
patch_cnt = 0;
for f = 1:1:numel(fn)
    fprintf('%d/%d\n', f, numel(fn));
    [p, n, e] = fileparts(fn{f});
    
    im = imread(fn{f});
    [h, w, d] = size(im);
    
    % Split the combined image into left and right
    imL = im(:, 1:w / 2, :);
    imR = im(:, w / 2 + 1:end, :);
    
    % Undo the camera distortion
    imL = undistortImage(imL, stereoParams.CameraParameters1);
    imR = undistortImage(imR, stereoParams.CameraParameters2);
    %     [imL, imR] = rectifyStereoImages(imL, imR, stereoParams, 'OutputView', 'valid');
    
    % Convert images to grayscale for cascade detector
    imgL = rgb2gray(imL);
    imgR = rgb2gray(imR);
    %     imoutL = imL;
    %     imoutR = imR;
    imoutL = repmat(imgL, [1 1 3]);
    imoutR = repmat(imgR, [1 1 3]);
    
    % Perform cone detection
    bboxL = step(detector, imgL);
    bboxR = step(detector, imgR);
    
    % Subtract the boundary around bboxes which was used for training
%     if ~isempty(bboxL)
%         bboxL(:, 1:2) = bboxL(:, 1:2) + BORDER;
%         bboxL(:, 3:4) = bboxL(:, 3:4) - 2 * BORDER;
%     end
%     if ~isempty(bboxR)
%         bboxR(:, 1:2) = bboxR(:, 1:2) + BORDER;
%         bboxR(:, 3:4) = bboxR(:, 3:4) - 2 * BORDER;
%     end
    
%     bboxL = filter_bboxes_energy(imgL, bboxL, RMS_MIN);
%     bboxR = filter_bboxes_energy(imgR, bboxR, RMS_MIN);
    
    
    
    
    % Draw tentatively detected bboxes
    imoutL = draw_bbox(imoutL, bboxL, [0 128 0], 0.5);
    imoutR = draw_bbox(imoutR, bboxR, [0 128 0], 0.5);
    
    % Compute cone reference points (centres)
    conesL = bbox_centroids(bboxL);
    conesR = bbox_centroids(bboxR);
    
    
    AA = zeros(size(conesL, 2), size(conesR, 2));
    cones3D = [];
    pairs_idx = [];
    pairs = [];
    pairs_err = [];
    pairs_h = [];
    
    P1 = cameraMatrix1';
    P2 = cameraMatrix2';
    for i = 1:size(conesL, 2)
        imoutL = draw_cross(imoutL, conesL(1, i), conesL(2, i), [128 128 0], 0.5);
    end
    for j = 1:size(conesR, 2)
        imoutR = draw_cross(imoutR, conesR(1, j), conesR(2, j), [128 128 0], 0.5);
    end
    for i = 1:size(conesL, 2)
        for j = 1:size(conesR, 2)
            %             [world, err] = triangulate(conesL(:, i)', conesR(:, j)', stereoParams);
            %             if err > 20, err = 1e10; end
            [world, err] = triangulate_point(conesL(:, i), conesR(:, j), P1, P2);
            AA(i, j) = err;
            
            if err > MAX_REPROJ_ERR, continue; end
            if world(3) < 0 || world(3) > MAX_Z, continue; end
            
            [bbox_world, bbox_err] = triangulate_bbox(bboxL(i, :), bboxR(j, :), P1, P2);
            height = 0.5 * (vnorm(bbox_world(:, 1) - bbox_world(:, 3)) + ...
                vnorm(bbox_world(:, 2) - bbox_world(:, 4)));
%             
%             if height > CONE_HEIGHT_MAX, continue; end;
%             if height < CONE_HEIGHT_MIN, continue; end;
            pairs_h = [pairs_h height];
            
            cones3D = [cones3D world(:)];
            pairs_idx = [pairs_idx [i; j]];
            pairs = [pairs [conesL(:, i); conesR(:, j)]];
            pairs_err = [pairs_err err];
%             imoutL = insertText(imoutL, bboxL(i, 1:2) + [bboxL(i, 3) * 0.5 bboxL(i, 4)], num2str(i), ...
%                 'TextColor', [255 255 128], 'BoxColor', [128 128 255], ...
%                 'AnchorPoint', 'CenterTop', 'BoxOpacity', 0.25, ...
%                 'Font', 'UbuntuMono-R', 'FontSize', 12);
%             imoutR = insertText(imoutR, bboxR(j, 1:2) + [bboxR(j, 3) * 0.5 bboxR(j, 4)], num2str(j), ...
%                 'TextColor', [255 255 128], 'BoxColor', [128 128 255], ...
%                 'AnchorPoint', 'CenterTop', 'BoxOpacity', 0.25, ...
%                 'Font', 'UbuntuMono-R', 'FontSize', 12);
            
            
            
%             reproj_bbox_L = project_points(bbox_world', cameraMatrix1');
%             reproj_bbox_R = project_points(bbox_world', cameraMatrix2');
%             
%             draw_line(imoutL, reproj_bbox_L(:, 1), reproj_bbox_L(:, 2), [255 0 0], 1);
%             draw_line(imoutL, reproj_bbox_L(:, 2), reproj_bbox_L(:, 4), [255 0 0], 1);
%             draw_line(imoutL, reproj_bbox_L(:, 1), reproj_bbox_L(:, 3), [255 0 0], 1);
%             draw_line(imoutL, reproj_bbox_L(:, 3), reproj_bbox_L(:, 4), [255 0 0], 1);
%             
%             draw_line(imoutR, reproj_bbox_R(:, 1), reproj_bbox_R(:, 2), [255 0 0], 1);
%             draw_line(imoutR, reproj_bbox_R(:, 2), reproj_bbox_R(:, 4), [255 0 0], 1);
%             draw_line(imoutR, reproj_bbox_R(:, 1), reproj_bbox_R(:, 3), [255 0 0], 1);
%             draw_line(imoutR, reproj_bbox_R(:, 3), reproj_bbox_R(:, 4), [255 0 0], 1);
            
        end
    end
    
    pairs_idx_old = pairs_idx;
    if ~isempty(pairs_idx)
        % Solve the assignment problem
        A = ones(max(pairs_idx(:))) * 100;
        for i = 1:size(pairs_idx, 2)
            A(pairs_idx(1, i), pairs_idx(2, i)) = pairs_err(i);% + (abs(pairs_h(i) - 45.0));
        end
        h = hungarian(A);
        [r, c] = find(h);
        
        pairs_idx_new = [];
        for i = 1:numel(c)
            if A(r(i), c(i)) == 100, continue; end
            pairs_idx_new = [pairs_idx_new [r(i); c(i)]];
        end
        pairs_idx = sortrows(pairs_idx_new')';%pairs_idx_new;
    end
    
%     if ~isempty(pairs_idx)
%         imoutL = draw_bbox(imoutL, bboxL(unique(pairs_idx(1, :)), :), [128 128 0], 0);
%         imoutR = draw_bbox(imoutR, bboxR(unique(pairs_idx(2, :)), :), [128 128 0], 0);
%         t = lineToBorderPoints(epipolarLine(stereoParams.FundamentalMatrix', pairs(3:4, :)'), size(imL));
%         draw_line(imoutL, t(:, 1:2)', t(:, 3:4)', [128 128 255], 0.5);
%         t = lineToBorderPoints(epipolarLine(stereoParams.FundamentalMatrix, pairs(1:2, :)'), size(imR));
%         draw_line(imoutR, t(:, 1:2)', t(:, 3:4)', [128 128 255], 0.5);
%     end
    
    if isempty(cones3D)
        reprojL = []; reprojR = [];
    else
        reprojL = project_points(cones3D', cameraMatrix1');
        reprojR = project_points(cones3D', cameraMatrix2');
    end
    
    c3D = [];
    for i = 1:size(pairs_idx, 2)
        imoutL = draw_cross(imoutL, reprojL(1, i), reprojL(2, i), [0 255 0], 1);
        idx = findrow(pairs_idx_old', pairs_idx(:, i)');%find(pairs_idx_old(1, :) == pairs_idx(1, i), 1);
        imoutL = insertText(imoutL, bboxL(pairs_idx(1, i), 1:2) + [bboxL(pairs_idx(1, i), 3) * 0.5 0], ...
            sprintf('%.0f %.0f %.0f\nh=%.1f e=%.1f', cones3D(1, idx), cones3D(2, idx), cones3D(3, idx), pairs_h(idx), pairs_err(idx)), ...
            'TextColor', [255 255 128], 'BoxColor', [128 128 255], ...
            'AnchorPoint', 'CenterBottom', 'BoxOpacity', 0.25, ...
            'Font', 'UbuntuMono-R', 'FontSize', 12);
        
        c3D = [c3D cones3D(:, idx)];
        imoutR = draw_cross(imoutR, reprojR(1, i), reprojR(2, i), [0 255 0], 1);
        imoutR = insertText(imoutR, bboxR(pairs_idx(2, i), 1:2), sprintf('%.0f', cones3D(3, i)), ...
            'TextColor', [255 255 128], 'BoxColor', [128 128 255], ...
            'AnchorPoint', 'LeftBottom', 'BoxOpacity', 0.6, ...
            'Font', 'UbuntuMono-R', 'FontSize', 12);
        
        depth = vnorm(cones3D(:, i));
        D = [D depth];
        H = [H bboxL(pairs_idx(1, i), 4)];
    end
    
    imout_both = imresize([imoutR imoutL], 2);
    %     imwrite(imout_both, ['out/' experiment '/' n '.jpg']);
    % open(vid);
    % writeVideo(vid, imout_both);
    % close(vid);
    
    set(0, 'CurrentFigure', 1);
    ax = gca;
    if isempty(ax.Children)
        sc(imout_both);
    else
        ax.Children(1).CData = imout_both;
    end
    drawnow;
    
    if 0
        set(0, 'CurrentFigure', 2);
        %         if isempty(cones3D)
        %             c3D = [];
        %         else
        %             c3D = cones3D(:, cones3D(3, :) > 0 & cones3D(3, :) < MAX_Z);
        %         end
        plotCamera('Location', [0 0 0], 'Orientation', eye(3), 'Size', 50);
        hold on
        plotCamera('Location', -stereoParams.TranslationOfCamera2, 'Orientation', stereoParams.RotationOfCamera2', 'Size', 50);
        if ~isempty(c3D)
            plot3(c3D(1, :), c3D(2, :), c3D(3, :), 'ko', 'MarkerSize', 10, ...
                'MarkerFaceColor', 'k');
        end
        hold off
        grid on
        grid minor
        axis equal
        view(-16, -16);
        xlim([-500 500]);
        ylim([-500 500]);
        zlim([0 1000]);
        drawnow;
        export_fig(['out/' experiment '/' n '_3D.png']);
    end
end



% Train two detectors: one for large, one for small cones?
