if 1
%     negfn_all = [list_files('../data/negative/all/*.jpg'); ...
%         list_files('../data/negative/all/*.png')];
    negfn_all = [glob('../../car_data/negative/**.jpg'); ...
        glob('../../car_data/negative/**.jpeg');
        glob('../../car_data/negative/**.png')];
    fprintf('Found %d negative images.\n', numel(negfn_all));
    negfn = {};
    warning('off')
    for i = 1:numel(negfn_all)
        info = imfinfo(negfn_all{i});
        if info.BitDepth ~= 24, continue; end
        negfn{end + 1} = negfn_all{i};
    end
    warning('on')
    % negfn = negfn_all;
    
    Nnegim = numel(negfn);
    fprintf('Of them %d are in colour.\n', Nnegim);
end


% 
% im = cell(Nnegim, 1);
% for i = 1:numel(im)
%     i
%     im{i} = imread(negfn{i});
% endf

Nneg = 100000;
Nper_image = ceil(Nneg / Nnegim);
% cw = 21; ch = 26;
cw = 17; ch = 23;
buf = zeros(ch, cw, 3, 'single');

% Xneg = zeros(cw * ch * 3, Nneg, 'single');

min_height_ratio = 0.020;
max_height_ratio = 0.125;

for i = 1:Nneg
    i
    % Read a random negative image
    im_idx = randi(Nnegim);
    im = imread(negfn{im_idx});
    [h, w, ~] = size(im);
    while h >= 1024
        h = h / 2; w = w / 2;
    end
    im = imresize(im, [h w]);
    [h, w, ~] = size(im);
    
    height = h * ((max_height_ratio - min_height_ratio) * rand() + min_height_ratio);
    width = cone_width_from_height(height);
    
    x = randi(w - ceil(width) + 1);
    y = randi(h - ceil(height) + 1);
    getwndbl_scale(buf, im, x, y, width, height);
    outfn = fullfile('../../car_data/local/negative_patches', sprintf('%06d.png', i));
    imwrite(uint8(buf), outfn);
end
