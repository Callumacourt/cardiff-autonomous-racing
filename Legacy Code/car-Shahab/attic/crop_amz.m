fn = list_files('data/amz/*.png');
for i = 1:numel(fn)
    [p, n, e] = fileparts(fn{i});
    im = imread(fn{i});
    cropped = im(271:810, 1:960, :);
    imwrite(cropped, [p '/cropped/' n e]);
end