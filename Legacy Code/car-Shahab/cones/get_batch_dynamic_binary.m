function [images, labels] = get_batch_dynamic_binary(imdb, batch)

cw = size(imdb.images.data, 2); ch = size(imdb.images.data, 1);
buf = zeros(ch, cw, size(imdb.images.data, 3), 'single');
% buf1 = zeros(ch, cw, size(imdb.images.data, 3), 'single');
N = numel(batch);
images = zeros(ch, cw, size(imdb.images.data, 3), N, 'single');


fraction_bg_dynamic = 0.3;
fraction_bg_static = 0.3;
Nbg_dynamic = round(fraction_bg_dynamic * N);
Nbg_static = round(fraction_bg_static * N);

min_height_ratio = 0.020;
max_height_ratio = 0.125;

labels = zeros(1, 1, 1, N);

for i = 1:Nbg_dynamic
    % Read a random negative image
    im_idx = randi(numel(imdb.negim));
    im = imdb.negim{im_idx};

    [h, w, ~] = size(im);
    
    height = h * ((max_height_ratio - min_height_ratio) * rand() + min_height_ratio);
    width = cone_width_from_height(height);
    
    x = randi(w - ceil(width) + 1);
    y = randi(h - ceil(height) + 1);
%     getwndbl_scale(buf, im, x, y, width, height);
    getwndnn(buf, im, x, y, width, height);
    images(:, :, :, i) = buf;
    
    labels(i) = 2;
end

idx_bg = find(imdb.images.label == 2 & imdb.images.set == 1);
images(:, :, :, Nbg_dynamic+1:Nbg_dynamic+Nbg_static) = ...
    imdb.images.data(:, :, :, idx_bg(randi(numel(idx_bg), [1 Nbg_static])));
labels(:, :, :, Nbg_dynamic+1:Nbg_dynamic+Nbg_static) = 2;

Nfg = N - Nbg_dynamic - Nbg_static;

correct_labels = imdb.images.label == 1;
idx_fg = find(correct_labels & imdb.images.set == 1);

take_fg = idx_fg(randi(numel(idx_fg), [1 Nfg]));

im_fg = imdb.images.data(:, :, :, take_fg) + randn(ch, cw, 3, numel(take_fg)) * 5;
a = 0.75; b = 1.5;
for i = 1:size(im_fg, 4)
    if rand() > 0.5
        [h, s, v] = rgb2hsv(im_fg(:, :, :, i));
        sat = a + (b-a) * rand();
        brt = a + (b-a) * rand();
        ns = clamp(s * sat, 0, 1);
        nv = clamp(v * brt, 0, 255);
        aa = hsv2rgb(cat(3, h, ns, nv));
        im_fg(:, :, :, i) = aa;
    end
end


% Block window
% for i = 1:size(im_fg, 4)
%     if rand() > 0.5
%         cc = randi(cw);
%         cr = randi(ch);
%         im_fg(max(1, cr - 2):min(ch, cr + 2), max(1, cc - 2):min(cw, cc + 2), :, i) = ...
%             rand(min(ch, cr + 2) - max(1, cr - 2) + 1, min(cw, cc + 2) - max(1, cc - 2) + 1, 3) * 255;
%     end
% end
labels_fg = imdb.images.label(take_fg);

% Flip vertically
for i = 1:size(im_fg, 4)
    if rand() > 0.75
        im_fg(:, :, :, i) = flipud(im_fg(:, :, :, i));
        labels_fg(i) = 2; % Becomes background
    end
end
images(:, :, :, Nbg_dynamic+Nbg_static+1:N) = im_fg;
labels(:, :, :, Nbg_dynamic+Nbg_static+1:N) = labels_fg;



