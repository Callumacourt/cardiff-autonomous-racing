path = '../../car_data/test_days/2019-12-11/recording0_calib_flipped';
path = '../../car_data/cones/fsuk19_calibration/calibration_track1_side1_before';
fn = list_files(fullfile(path, '*.jpg'), 1);

path_L = fullfile(path, 'L');
path_R = fullfile(path, 'R');

if ~exist(path_L, 'dir')
    mkdir(path_L);
end
if ~exist(path_R, 'dir')
    mkdir(path_R);
end

for i = 1:numel(fn)
    fprintf('%d / %d\n', i, numel(fn));
    im = imread(fn{i});
    [L, R] = split_stereo_image(im);
    [p, n, e] = fileparts(fn{i});
    imwrite(L, fullfile(path_L, [n '.png']));
    imwrite(R, fullfile(path_R, [n '.png']));
end
