fn = list_files('patches/*.png');

N = numel(fn);

for i = 1:N
    im = imread(fn{i});
    [p, n, e] = fileparts(fn{i});
    if blue(i)
        imwrite(im, [fullfile('patches_blue', n) e]);
    end
    if yellow(i)
                imwrite(im, [fullfile('patches_yellow', n) e]);
    end
end