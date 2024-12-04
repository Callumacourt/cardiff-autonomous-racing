fn = list_files('../data/fsuk17/*.png');

for i = 1:numel(fn)
    i
    [p, n, e] = fileparts(fn{i});
    im = imread(fn{i});
    im = im(271:271+540-1, 481:481+960-1, :);
    imwrite(im, fullfile(p, 'cropped', [n e]));
end