im = imread('../data/amz/002277.png');
[h, w, d] = size(im);
im = im2double(im);

d = 800;
x = [    426
    97
   521
   1000]';
y =[    129
   292
   127
   302]';


yn = [y(1) h y(1) h];
xn = [x(2) x(2) x(4) x(4)];

alpha = 1.3
xn = alpha * xn + (1 - alpha) * x;
xy = alpha * yn + (1 - alpha) * y;
% xn = x;

H1 = vgg_H_from_x_lin([x; y; ones(1, numel(x))], [xn; yn; ones(1, numel(x))]);
H = homography_solve([xn; yn], [x; y]);
% H = inv(H);
[xx yy] = meshgrid(1:w, 1:h);

c = [xx(:) yy(:)]';

% cn = inv(H) * c;
cn = homography_transform(c, H);
fn = list_files('../data/amz/*.png');

for i = 2277:2277%numel(fn)
    im = im2double(imread(fn{i}));
tic
% c1 = interp2(im(:, :, 1), reshape(cn(1, :), h, w), reshape(cn(2, :), h, w));
% c2 = interp2(im(:, :, 2), reshape(cn(1, :), h, w), reshape(cn(2, :), h, w));
% c3 = interp2(im(:, :, 3), reshape(cn(1, :), h, w), reshape(cn(2, :), h, w));
% A = cat(3, c1, c2, c3);
A = im_homography(im, H);
toc
figure(1); clf;
sc([imresize(A, 0.5, 'nearest'); imresize(im, 0.5, 'nearest')]);

drawnow;
end

% n = inv(H) * [x; y; ones(1, numel(x))];
n = homography_transform([x; y], inv(H));

figure(2); clf;
sc(A);
hold on
plot(n(1, :), n(2, :), 'y*');
hold off

