if 0
    imdb = load('cones_23_17_rgb_padded.mat');
end
im = imdb.images.data;
labels = imdb.images.label;

rows = 22;
cols = 20;


page = 0;

for label = [1, 2, 4]
    im_this = im(:, :, :, labels == label);
    pos = 1;
    while true
        G = imgallery(im_this(:, :, :, pos:min(size(im_this, 4), pos + rows * cols - 1)), ...
            'rows', rows, 'cols', cols, 'gap', 2);
        imwrite(G ./ 255, sprintf('out/cones/gallery%04d.png', page));
        page = page + 1;
        pos = pos + rows * cols;
        if pos > size(im_this, 4), break; end
    end
end
% A4: 210x297
% Image: 180x267
