% im = rgb2gray(imread('lenna.png'));
im = imread('lenna.png');
[h, w, d] = size(im);

buf = zeros([128 128 size(im, 3)], 'single');
buf1 = zeros([128 128 size(im, 3)], 'single');
tic
getwndbl_scale(buf1, im, 1, 1, 512, 512);
toc
tic
getwndnn(buf, im, 1, 1, 512, 512);
toc
def = imresize(double(im), [size(buf, 1) size(buf, 2)], 'bilinear', 'antialiasing', false);
def = imresize(double(im), [size(buf, 1) size(buf, 2)], 'nearest', 'antialiasing', false);

fig(1); sc(buf);
fig(2); sc(def);
fig(3); sc(buf - def);








N = 300000;
rng(1);
x1 = randi(w, [1 N]);
x2 = randi(w, [1 N]);
x1x2 = sort([x1; x2]);
y1 = randi(h, [1 N]);
y2 = randi(h, [1 N]);
y1y2 = sort([y1; y2]);

w = x1x2(2, :) - x1x2(1, :) + 1;
h = y1y2(2, :) - y1y2(1, :) + 1;
b = [x1x2(1, :); y1y2(1, :); w; h];

% Check correctness
buf = zeros([32 24 size(im, 3)], 'single');
% for i = 1:size(b, 2)
%     wnd = imresize(double(im(b(2, i):b(2, i)+b(4, i)-1, b(1, i):b(1, i)+b(3, i)-1)), ...
%         [32 24], 'bilinear', 'antialiasing', false);
%     getwndbl_scale(buf, im, b(1, i), b(2, i), b(3, i), b(4, i));
%     
%     d = abs(wnd - buf);
%     err = max(max(d));
%     if err > 5.0 && nnz(abs(d) > 1) > 100 && b(3, i) > 10 && b(4, i) > 10;
%         error('Images differ.');
%     end        
% end


% Time Matlab
% tic
% for i = 1:size(b, 2)
%     wnd = imresize(double(im(b(2, i):b(2, i)+b(4, i)-1, b(1, i):b(1, i)+b(3, i)-1)), ...
%         [32 24], 'bilinear', 'antialiasing', false);
% end
% dt1 = toc;
% fprintf('%.4f ms/image.\n', 1000 * dt1 / N);

% Time improved implementation
tic
for i = 1:size(b, 2)
%     getwndbl_scale(buf, im, b(1, i), b(2, i), b(3, i), b(4, i));
        getwndnn(buf, im, b(1, i), b(2, i), b(3, i), b(4, i));

end
dt2 = toc;

fprintf('%.4f microsec/image.\n', 1e6 * dt2 / N);
% fprintf('Speedup: %.2f\n', dt1 / dt2);

return




buf = zeros(128);
getwndbl_scale(buf, im, 1, 1, 512, 512);
def = imresize(double(im), size(buf), 'bilinear', 'antialiasing', false);

fig(1); sc(buf);
fig(2); sc(def);
fig(3); sc(buf - def);
return


if 0
    [imfn, bb] = load_annotated_cones();
end
cw = 24; ch = 32;
buf = zeros(ch, cw);

im = rgb2gray(imread('../data/cones/amz/every10/000005.png'));
b = bb{1}(1, :);

% im = uint8(checkerboard(4, 8));
% im = uint8(randi(256, [128 128]) - 1);
% im = uint8(repmat(1:8, 8, 1))';


% b = [0    1 1 8 8];
tic
wnd = im(b(3):b(3)+b(5)-1, b(2):b(2)+b(4)-1, :);
wnd
wnd = imresize(double(wnd), [ch cw], 'bilinear', 'antialiasing', false);
% wnd = bilinearInterpolation(double(wnd), [ch cw]);
toc

tic
getwndbl_scale(buf, im, b(2), b(3), b(4), b(5));
toc

fig(1);
sc([buf wnd abs(buf - double(wnd))]);
buf
wnd
