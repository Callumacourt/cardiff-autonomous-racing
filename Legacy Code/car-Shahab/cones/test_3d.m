if 1
%     net = load('good_cnns/cnn-experiment-cones-np-23x17-8-8-8-16-4classes/cones_cnn.mat');
        net = load('cnn-experiment-cones-np-23x17-6-4-6-6-4classes-do00-bn/cones_cnn.mat');
    
    %     if isstruct(net)
    %         net = net.net;
    %         net.layers(end) = [] ;
    %         net.layers(find(cellfun(@(x)strcmp(x.type, 'dropout'), net.layers))) = []; %#ok<FNDSB>
    %     end
    net = vl_simplenn_move(net, 'gpu');
    
    fn = list_files('~/research/car_data/test_days/2019-12-11/recording0_flipped/*.jpg');
    calib = load('../../car_data/test_days/2019-12-11/recording0_calib_flipped/stereoParams.mat');
    GtoC = load('~/research/car_data/test_days/2019-12-11/recording0_calib_flipped/GtoC.mat'); GtoC = GtoC.GtoC;
    stereoParams = calib.stereoParams;
    P1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0])';
    P2 = cameraMatrix(stereoParams.CameraParameters2, ...
        stereoParams.RotationOfCamera2, stereoParams.TranslationOfCamera2)';
    cameraMatrix1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0]);
    cameraMatrix2 = cameraMatrix(stereoParams.CameraParameters2, eye(3), [0 0 0]);%...
end
scale = 1;
scales = 1.5  .^ -(0:3); %linspace(1, 0.125, 4);
dev = gpuDevice();

info = imfinfo(fn{1});
w = info.Width / 2; h = info.Height;

% Points at which to evaluate the world
[xx, yy, zz] = meshgrid(-1000:2:1000, ...
    2000:-2:190, 20 + (-5:1:5));
X_world = [xx(:) yy(:) zz(:)]';
X_car = rigid(GtoC, X_world)';
proj_l = project_points(X_car, P1) + 1;
proj_r = project_points(X_car, P2) + 1;


%     fig(1);
%     sc(imL);
%     hold on
%         plot(proj_l(1, :), proj_l(2, :), 'r.');
%     hold off
%     break

proj_l = round(proj_l);
proj_r = round(proj_r);
within_l = proj_l(1, :) > 0 & proj_l(1, :) <= w & ...
    proj_l(2, :) > 0 & proj_l(2, :) <= h;
within_r = proj_r(1, :) > 0 & proj_r(1, :) <= w & ...
    proj_r(2, :) > 0 & proj_r(2, :) <= h;
within_both = within_l & within_r;

% For visualisation
wi_l = sum(reshape(within_l, size(xx)), 3) > 0;
wi_r = sum(reshape(within_r, size(xx)), 3) > 0;

idx_l = sub2ind([h w], proj_l(2, within_both), proj_l(1, within_both));
idx_r = sub2ind([h w], proj_r(2, within_both), proj_r(1, within_both));
for frame = 1080% 3925% 3800:numel(fn)
    im = imread(fn{frame});
    [h, w, d] = size(im);
    % Split the combined image into left and right
    imL_distorted = im(:, 1:w / 2, :);
    imR_distorted = im(:, w / 2 + 1:end, :);
    % Undo the camera distortion
    imL = undistortImage(imL_distorted, stereoParams.CameraParameters1);
    imR = undistortImage(imR_distorted, stereoParams.CameraParameters2);
    imLg = rgb2gray(im2double(imL));
    imRg = rgb2gray(im2double(imR));
    [h, w, d] = size(imL);
    tic
    Cl = detect_cnn_multiscale(imL, net, scale, scales);
    Cr = detect_cnn_multiscale(imR, net, scale, scales);
    wait(dev); toc
    
    
    
    %     proj_l(:, ~within_image) = [];
    %     proj_r(:, ~within_image) = [];
    
    Cl = gather(max(Cl, [], 3));
    Cr = gather(max(Cr, [], 3));
    Cl(Cl >= 0.95) = 1;
    Cr(Cr >= 0.95) = 1;
    Cl(Cl < 0.95) = 0;
    Cr(Cr < 0.95) = 0;
    
    % Sample the coneness maps
    val = Cl(idx_l);
    Cwl = zeros(1, size(proj_l, 2));
    Cwl(within_both) = val;
    Cwl = reshape(Cwl, size(xx));
    Cwl = max(Cwl, [], 3);
    
    val = Cr(idx_r);
    Cwr = zeros(1, size(proj_r, 2));
    Cwr(within_both) = val;
    Cwr = reshape(Cwr, size(xx));
    Cwr = max(Cwr, [], 3);
    
    
    %     im2d = im2double(im);
    im2d = [cat(3, imLg, max(imLg, Cl), imLg) cat(3, imRg, max(imRg, Cr), imRg)];
    Cwl(~wi_l) = 0.5;
    Cwr(~wi_r) = 0.5;
    Cw = Cwl + Cwr;
    Cw(~(wi_l & wi_r)) = 0.5;
    im3d = sc([Cwl Cwr Cw]);
    new_h = size(im3d, 1) * size(im2d, 2) / size(im3d, 2);
    im3d = imresize(im3d, [new_h, size(im2d, 2)]);
    
    im_disp = [im2d; im3d];
    fig(1);
    sc(im_disp);
    drawnow;
    %         break
end
