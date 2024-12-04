if 0
fn = list_files('../data/amz/0*.png');

pix = [];

for i = 1:4:numel(fn)
    i
    im = im2double(imread(fn{i}));
    p = im2pix(im);
    pix = [pix p(:, randi(size(p, 2), 1, 1000))];
end
end

hsv = rgb2hsv(pix')';
[cl, CTR] = kmeans(hsv(:, :)', Nc, 'replicates', 1);