% function [am, CONF] = train_cone_am(varargin)

opt.ch = 26;
opt.cw = [];
opt.colour = true;
opt.labels = [0, 1];
opt.save = true;
opt.mask = false;
opt.pad = [];
opt.simplify = false;
opt.replicates = 30;
opt.keep = [];
opt.energy = 0.95;

try
    opt = parseargs(opt, varargin{:});
end
if isempty(opt.cw)
    opt.cw = round(cone_width_from_height(opt.ch));
end
opt.name = am_name(opt);


if opt.mask
    mask = imread(sprintf('mask_%02dx%02d.png', opt.ch, opt.cw)) > 0;
    if opt.colour
        mask = repmat(mask, [1 1 3]);
    end
else
    if opt.colour
        mask = true(opt.ch, opt.cw, 3);
    else
        mask = true(opt.ch, opt.cw);
    end
end
mask = mask(:);

am = struct;
if 1
    fprintf('Loading positive examples from annotations...');
    [X, L, Xother, fn] = load_positive_patches(opt.labels, 'cw', opt.cw, 'ch', opt.ch, ...
        'colour', opt.colour, 'pad', opt.pad);
    fprintf('done\n');
end

if 1
    % Load negative patches
    fprintf('Loading negative examples...');
    Xneg = load('patches_26_21_neg_rgb_100000'); Xneg = Xneg.Xneg(:, 1:10:end);
    Xneg_mined = load('patches_26_21_neg_rgb_89179_mined'); Xneg_mined = Xneg_mined.Xneg(:, 1:1:end);
    Xneg = [Xneg Xneg_mined];
    fprintf('done\n');
    % Resize if necessary
    if size(Xneg, 1) ~= opt.ch * opt.cw * 3
        Xneg = resize_patches(Xneg, 32, 24, opt.ch, opt.cw, opt.colour);
    end
end

%%%
% X = X(1:size(X, 1) / 3, :);
% Xother = Xother(1:size(Xother, 1) / 3, :);
% Xneg = Xneg(1:size(Xneg, 1) / 3, :);
% mask = mask(1:size(mask, 1) / 3, :);
%%%

% x = [X(mask, :) Xneg(mask, :)];
x = double([X]);
% x = double([X Xother Xneg]);
fprintf('Performing PCA...');
[am.B, am.ev, am.avg] = kspca(x);
fprintf('done\n');

if isempty(opt.keep)
en = cumsum(am.ev) / sum(am.ev);
am.keep = find(en > opt.energy, 1);
fprintf('Keeping %d eigenvectors to account for %.1f%% of eigenenergy.\n', ...
    am.keep, opt.energy * 100);
else
    am.keep = opt.keep;
    fprintf('Keeping %d eigenvectors.\n', am.keep);
end
am.cw = opt.cw;
am.ch = opt.ch;
am.B = single(am.B(:, 1:am.keep));
am.avg = single(am.avg);
% am.mask = mask;


proj = (am.B(:, 1:am.keep)' * subcol(X(mask, :), am.avg))';
am.sd = single(std(proj)');
proj_original = proj';
proj_min = min(proj);
proj_max = max(proj);
am.a = single(1 ./ (proj_max - proj_min));
am.b = single(-proj_min .* am.a);

proj = proj .* repmat(am.a, size(proj, 1), 1) + ...
    repmat(am.b, size(proj, 1), 1);

proj_neg = (am.B(:, 1:am.keep)' * ...
    subcol([Xother(mask, :) Xneg(mask, :)], am.avg))';
proj_neg = proj_neg .* repmat(am.a, size(proj_neg, 1), 1) + ...
    repmat(am.b, size(proj_neg, 1), 1);

if numel(opt.labels > 1)
    lab = L' * 2 - 1;
    [mappedX, mapping] = lda(proj_original', lab, 1);
    am.lda_B = mapping.M;
    am.lda_avg = mapping.mean;
end

% colours = [mean(X(1:size(X, 1) / 3, :));
%            mean(X(1:size(X, 1) / 3 + 1:2 * size(X, 1) / 3, :))
%            mean(X(1:2 * size(X, 1) / 3 + 1:end, :))];
% colours_other = [mean(Xother(1:size(Xother, 1) / 3, :));
%            mean(Xother(1:size(Xother, 1) / 3 + 1:2 * size(Xother, 1) / 3, :))
%            mean(Xother(1:2 * size(Xother, 1) / 3 + 1:end, :))];
% colours_neg = [mean(Xneg(1:size(Xneg, 1) / 3, :));
%            mean(Xneg(1:size(Xneg, 1) / 3 + 1:2 * size(Xneg, 1) / 3, :))
%            mean(Xneg(1:2 * size(Xneg, 1) / 3 + 1:end, :))];       
% proj = [proj colours' ./ 255];
% proj_neg = [proj_neg [colours_other colours_neg]' ./ 255];

figure(1); clf;
whitebg('black');
hold on
col = [1.0 1.0 0.0; 0.0 0.0 1.0; 0.0 1.0 0.0];
v1 = 1; v2 = 2;
plot(proj_neg(:, v1), proj_neg(:, v2), '.', 'Color', [0.5 0.5 0.5], 'MarkerSize', 1);
for i = 0:2
    plot(proj(L == i, v1), proj(L == i, v2), '.', 'Color', col(i + 1, :));
end
drawnow;
grid on
hold off

% figure(2); clf;
% whitebg('black');
% hold on
% col = [1.0 1.0 0.0; 0.0 0.0 1.0; 0.0 1.0 0.0];
% % plot(proj_neg(:, v1), proj_neg(:, v2), '.', 'Color', [0.5 0.5 0.5], 'MarkerSize', 1);
% for i = 0:2
%     plot(colours(1, L == i), colours(2, L == i), '.', 'Color', col(i + 1, :));
% end
% drawnow;
% grid on
% hold off
% figure(2); clf;
% sc(reshape(am.B, am.ch, am.cw, 3, []))



data = double([proj; proj_neg]);
% lab = [ones(1, size(proj, 1)) zeros(1, size(proj_neg, 1))]';

cost = [0 1; 10 0];
lab = [L == 0 zeros(1, size(proj_neg, 1))]';
[am.svm_vectors, am.svm_alphas, am.svm_bias, am.svm_scale] = ...
    train_svm(data, lab, 'kernel_scale', 0.6484, 'C', 8, 'cost', cost, 'simplify', ...
    opt.simplify, 'Nsv', 20);

lab = [L == 1 zeros(1, size(proj_neg, 1))]';
[am.bsvm_vectors, am.bsvm_alphas, am.bsvm_bias, am.bsvm_scale] = ...
    train_svm(data, lab, 'kernel_scale', 0.8409, 'C', 16, 'cost', cost, 'simplify', ...
    opt.simplify, 'Nsv', 29);

% if numel(opt.labels) == 2
%     [am.csvm_vectors, am.csvm_alphas, am.csvm_bias, am.csvm_scale] = ...
%         train_svm(proj, L, 'kernel_scale', kernel_scale, 'simplify', false, 'Nsv', 3);
% end

am.name = opt.name;
am.colour = opt.colour;
if opt.save
    save([am.name '.mat'], '-struct', 'am', '-v6');
end


% fig(1);
% hold on
% sv = svm.IsSupportVector;
% plot(data(sv, v1), data(sv, v2), 'r.');
% % plot(am.svm_vectors(1, :), am.svm_vectors(2, :), 'go');
% hold off


% figure(2); clf;
% sc(reshape(B, 32, 24, 3, []))

% return

% With only 0
% 0.9850


% AUGMENT DATA BY SHIFTING AND SLIGHT ROTATIONS
% TRY GRAYSCALE ONLY MODEL
% THUNDERSVM
% SV regression to refine cone position!
% Try smaller sizez (e.g. 16x14 like in CD) and either with pca or directly
% see effect
% LS-Svm (toolbox)
% Train cascade detector with square windows to minimise the effect of
% aspect distortion
% Some simple method to detect cone centre? e.g. MSER (see vl_feat)
% Move convolution filters to constant memory
