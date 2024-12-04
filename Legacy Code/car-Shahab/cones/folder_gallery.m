if 0
fn = list_files('../../car_data/negative_hard/*.png');

rows = 60;
cols = 134;

I = zeros(23, 17, 3, numel(fn), 'uint8');
for i = 1:numel(fn)
    im = imread(fn{i});
    I(:, :, :, i) = im;
end
end

page = 0;
pos = 1;
GG = [];
while true
    G = imgallery(I(:, :, :, pos:min(size(I, 4), pos + rows * cols - 1)), ...
        'rows', rows, 'cols', cols, 'gap', 2);
%     imwrite(G ./ 255, sprintf('out/cones/gallery%04d.png', page));
    if isempty(GG)
        GG = G;
    else
        GG = cat(4, GG, G);
    end
    page = page + 1;
    pos = pos + rows * cols;
    if pos > size(I, 4), break; end
end
