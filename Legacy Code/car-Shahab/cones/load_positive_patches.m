function [X, L, X_other, fn, bboxes] = load_positive_patches(labels, varargin)

opt.cw = 24;
opt.ch = 32;
opt.colour = true;
opt.pad = [];
opt = parseargs(opt, varargin{:});
opt.min_height = 13;

[imfn, bb] = load_annotated_cones('augmented', false);

% Filter bounding boxes by size
for i = 1:numel(bb)
    b_filt = [];
    b = bb{i};
    for j = 1:size(b, 1)
        if b(j, 5) >= opt.min_height
            b_filt = [b_filt; b(j, :)];
        end
    end
    bb{i} = b_filt;
end


Nbb = sum(cellfun(@numel, bb) / 5);
if opt.colour
    cc = 3;
else
    cc = 1;
end
% X = zeros(opt.cw * opt.ch * cc, Nbb, 'single');
% X_flipped = zeros(opt.cw * opt.ch * cc, Nbb, 'single'); % Flipped
XX = zeros(opt.cw * opt.ch * cc, Nbb * numel(opt.pad), 'single');
XX_flipped = zeros(opt.cw * opt.ch * cc, Nbb * numel(opt.pad), 'single'); % Flipped
XX_shifted = zeros(opt.cw * opt.ch * cc, Nbb * numel(opt.pad) * 4, 'single'); % Shifted
L = zeros(1, Nbb * numel(opt.pad)); % Labels

% Allocate buffer into which image patches will be sampled
buf = zeros(opt.ch, opt.cw, cc, 'single');

fn = cell(Nbb, 1);
count = 1;
shifted_count = 1;
% Iterate through all images
last_fn = '';
bboxes = [];
for i = 1:numel(bb)
    if ~strcmp(last_fn, imfn{i})
        try
            im = imread(imfn{i});
        catch
            im = imread(replace_ext(imfn{i}, '.jpg'));
        end
        last_fn = imfn{i};
    end
    if ~opt.colour && size(im, 3) == 3
        im = rgb2gray(im);
    end
    b = bb{i};
    %     if ~isempty(opt.pad)
    %         b = pad_bbox(b, opt.pad);
    %     end
    for pad = opt.pad
        if pad == 1
            b_padded = b;
        else
            b_padded = pad_bbox(b, pad);
        end
        % Iterate through all bboxes in this image
        for j = 1:size(b_padded, 1)
            
            getwndbl_scale(buf, im, b_padded(j, 2), b_padded(j, 3), b_padded(j, 4), b_padded(j, 5));
            %         fig(1); sc(buf)
            XX(:, count) = buf(:);
            buff = fliplr(buf);
            XX_flipped(:, count) = buff(:);
            L(count) = b_padded(j, 1);
            fn{count} = imfn{i};
            bboxes = [bboxes; b_padded(j, :)];
            count = count + 1;
            
            % Shifted bbox
%             getwndbl_scale(buf, im, b_padded(j, 2), b_padded(j, 3) - 0.25 * b_padded(j, 5), b_padded(j, 4), b_padded(j, 5));
%             XX_shifted(:, shifted_count) = buf(:); shifted_count = shifted_count + 1;
%             buff = fliplr(buf);
%             XX_shifted(:, shifted_count) = buff(:); shifted_count = shifted_count + 1;
            
            getwndbl_scale(buf, im, b_padded(j, 2), b_padded(j, 3) - 0.3 * b_padded(j, 5), b_padded(j, 4), b_padded(j, 5));
            XX_shifted(:, shifted_count) = buf(:); shifted_count = shifted_count + 1;
            buff = fliplr(buf);
            XX_shifted(:, shifted_count) = buff(:); shifted_count = shifted_count + 1;
            
            getwndbl_scale(buf, im, b_padded(j, 2), b_padded(j, 3) + 0.3 * b_padded(j, 5), b_padded(j, 4), b_padded(j, 5));
            XX_shifted(:, shifted_count) = buf(:); shifted_count = shifted_count + 1;
            buff = fliplr(buf);
            XX_shifted(:, shifted_count) = buff(:); shifted_count = shifted_count + 1;
        end
    end
end

take = false(size(L));
for i = 1:numel(labels)
    take = take | (L == labels(i));
end
other = ~take;
% fprintf('%f\n', sum(XX(:)));

X = [XX(:, take) XX_flipped(:, take)];
X_other = [XX(:, other) XX_flipped(:, other), XX_shifted];
% X_other = [XX(:, other) XX_flipped(:, other)];

fn = fn(take);
bboxes = bboxes(take, :);
L = L(take);
L = [L L];
