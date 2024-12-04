% Xy = load('Xyellow.mat'); Xy = Xy.X;
% Xb = load('Xblue.mat'); Xb = Xb.X;
opt.ch = 26;
opt.cw = 21;
opt.colour = true;
opt.labels = [0, 1];
opt.pad = [];

if 0
[X, L, Xother, fn] = load_positive_patches(opt.labels, 'cw', opt.cw, 'ch', opt.ch, ...
        'colour', opt.colour, 'pad', opt.pad);
end

Xy = X(:, L == 0);
Xb = X(:, L == 1);

ch = 26; cw = 21;
% mask = imread(sprintf('mask_%02dx%02d.png', ch, cw)) > 0;
% mask = repmat(mask, [1 1 3]);
% mask = mask(:);
% 
% Xy = Xy(mask, :);
% Xb = Xb(mask, :);

pitch = size(Xy, 1) / 3;
r1 = Xy(1:pitch, :);
g1 = Xy(pitch+1:2*pitch, :);
b1 = Xy(2*pitch+1:end, :);
r2 = Xb(1:pitch, :);
g2 = Xb(pitch+1:2*pitch, :);
b2 = Xb(2*pitch+1:end, :);

y = [r1(:) g1(:) b1(:)]';
b = [r2(:) g2(:) b2(:)]';
y = y(:, 1:10:end);
b = b(:, 1:10:end);
% fig(1); clf;
% 
% plot3(y(1, 1:10:end), y(2, 1:10:end), y(3, 1:10:end), 'y.');
% hold on
% plot3(b(1, 1:10:end), b(2, 1:10:end), b(3, 1:10:end), 'b.');
% hold off
% xlabel('red'); ylabel('green'); zlabel('blue');
% grid on


X = [y'; b'];
lab = [-ones(size(y, 2), 1); ones(size(b, 2), 1)];
[mappedX, mapping] = lda(X ./ 255, lab, 1);
B = mapping.M;
avg = mapping.mean(:);

im = im2double(imread('../data/local/amz/000001.png'));
% im = im2double(imread('/home/coriolan/research/cr/data/cones/single_lap/frame0000.png'));
imr = im(:, :, 1);
img = im(:, :, 2);
imb = im(:, :, 3);

X = [imr(:) img(:) imb(:)]';


[x, y, z] = meshgrid(linspace(0, 1), linspace(0, 1), linspace(0, 1));
xx = [x(:) y(:) z(:)]';
a = B' * xx - B' * avg;

hi = max(a);
lo = min(a);
c = (-B' * avg - lo) / (hi - lo);
k = (B' / (hi - lo));
pred = k * X  + c;

pred = reshape(pred, size(im, 1), size(im, 2), []);
fig(1); sc(im);
% fig(4); sc(pred);

fig(2);
a = max(pred, 1 - pred);
a(a < 0.5) = 0;
a(a >= 0.5) = min(1, a(a >= 0.5) * 1.5);

sc(cat(3, a, a, a) .* im2double(im));
    
fig(3); sc(rgb2gray(im));
fig(4);
sc(a .* rgb2gray(im2double(im)));
fig(5); sc(pred);
