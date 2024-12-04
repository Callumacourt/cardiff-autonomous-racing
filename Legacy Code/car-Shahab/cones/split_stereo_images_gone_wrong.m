fn = dir('/home/kwantom/Documents/cr/cones/image_recordings/*.png'); %make sure to change the filepath here accordingly
addpath('/home/kwantom/Documents/cr/cones/image_recordings')

for i = 1:numel(fn)

    fprintf('%d / %d\n', i, numel(fn));
    im = imread(fn(i).name);
    [L, R] = split_stereo_image(im);
    %[p, n, e] = fileparts(fn{i});
    imwrite(L, [fullfile('/home/kwantom/Documents/cr/cones/image_recording', ['L' fn(i).name])]);
    imwrite(R, [fullfile('/home/kwantom/Documents/cr/cones/image_recording', ['R' fn(i).name])]);
end