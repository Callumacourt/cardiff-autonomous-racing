fn = list_files('alignment/patches.orig/*.png');
for i = 1:numel(fn)
    [p, n, e] = fileparts(fn{i});
    after = fullfile('alignment', 'patches', [n e]);
    im1 = imread(fn{i});
    im2 = imread(after);
    im = imresize([im1 im2], 2);
    imwrite(im, fullfile('alignment', 'both', [n e]));
end
