im = imread('../data/amz/000001.png');

t = 100; l = 200; w = 64; h = 128;

bw = 32; bh = 64;

tic
buf = imresize(im(t:t + h - 1, l:l + w - 1, :), [bh bw]);
toc