opt.ch = 23;
opt.cw = 17;
opt.colour = true;
opt.labels = [0, 1, 3];
opt.pad = linspace(1, 1.25, 4);

if isempty(opt.cw)
    opt.cw = round(cone_width_from_height(opt.ch));
end

if 1
    fprintf('Loading positive examples from annotations...');
    [X, L, Xother, fn, bb] = load_positive_patches(opt.labels, 'cw', opt.cw, 'ch', opt.ch, ...
        'colour', opt.colour, 'pad', opt.pad);
    fprintf('done\n');
end

if 1
    % Load negative patches
    fprintf('Loading negative examples...');
    Xneg = load('patches_23_17_rgb_100000_negative.mat');
    Xneg_mined = load('patches_23_17_rgb_159382_mined.mat');
%     Xneg = [Xother Xneg_mined.Xneg(:, 1:1:end)];
    Xneg = [Xneg.Xneg(:, 1:1:end) Xother Xneg_mined.Xneg(:, 1:1:end)];
    
%     Xneg = [Xother Xneg_mined.Xneg(:, 1:1:end)];
%     Xneg = [Xneg.Xneg(:, 1:1:end) Xother];
%     Xneg = [Xneg.Xneg(:, 1:1:end) Xneg_mined.Xneg(:, 1:1:end)];
%     Xneg = [Xneg.Xneg(:, 1:1:end) Xother];
    fprintf('done\n');
end

% X = X(1:size(X, 1) / 3, :);
% Xneg = Xneg(1:size(Xneg, 1) / 3, :);
channels = 3;

imdb = struct;
% imdb.classes = {'yellow', 'blue', 'bg'};
imdb.classes = {'yellow', 'blue', 'background', 'red'};
imdb.images = struct;
imdb.images.data = reshape([X Xneg], opt.ch, opt.cw, channels, []);
imdb.images.label = [L ones(1, size(Xneg, 2))*2] + 1;
% imdb.images.label = [zeros(size(L)) ones(1, size(Xneg, 2))] + 1;

imdb.images.set = ones(size(imdb.images.label));
imdb.images.set(1:10:end) = 2;
imdb.images.fn = fn;
imdb.images.bb = bb;

negfn = find_negative_images();
imdb.negfn = negfn;
