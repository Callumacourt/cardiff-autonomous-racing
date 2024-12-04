if 1
    fn = list_files('../data/recording.261019/*.jpg');
    calib = load('../data/recording.261019/calibration.261019.mat');
    stereoParams = calib.stereoParams;
    det = load('../data/recording.261019/board.261019.txt', '-ascii');
end



N = numel(fn);
[x, y] = meshgrid(0:10:500, 0:10:700);
X = [x(:) y(:) zeros(numel(x), 1)]';
for i = 1:numel(fn)
    im = imread(fn{i});
    [h, w, d] = size(im);
    
    % Split the combined image into left and right
    imL = im(:, 1:w / 2, :);
    imR = im(:, w / 2 + 1:end, :);
    % Undo the camera distortion
    imL = undistortImage(imL, stereoParams.CameraParameters1);
    imR = undistortImage(imR, stereoParams.CameraParameters2);
    
    t = det(i, :);
    rotl = rodrigues(t(2:4)');
    transl = t(5:7)';
    rotr = rodrigues(t(9:11)');
    transr = t(12:14)';

    
    
   [proj_l, proj_r] = world_to_stereo(X, stereoParams, rotl, transl, t(1), rotr, transr, t(8));
    
    
    fig(1); sc(imL);
    if ~isempty(proj_l)
        hold on
        plot(proj_l(1, :), proj_l(2, :), 'g.');
        hold off
    end
    
    
    fig(2); sc(imR);
    if ~isempty(proj_r)
        hold on
        plot(proj_r(1, :), proj_r(2, :), 'g.');
        hold off
    end
    
    drawnow;
    
    
end