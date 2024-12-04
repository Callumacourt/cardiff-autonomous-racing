if 1
    fn = list_files('../../car_data/cones/amz/every10/*.png');
    net = load('cnn-experiment-cones/cones_cnn.mat');
    net = vl_simplenn_move(net, 'gpu');
    
end
im = imread(fn{1});
% new_w = ceil(size(im, 2) / 18) * 18;
% new_h = ceil(size(im, 1) / 24) * 24;
% im_new = zeros(new_h, new_w, size(im, 3), 'like', im);
% im_new(1:size(im, 1), 1:size(im, 2), :) = im;
% im = im_new;

imcv = matlab2opencv3(im);
buf = zeros(24, 18, 3, 'single');
[imh, imw, channels] = size(im);

F1 = single(gather(net.layers{1}.weights{1}));
B1 = single(gather(net.layers{1}.weights{2}));
im_gpu = gpuArray(single(im));

tic
res = vl_simplenn(net, im_gpu, [], [], 'ConserveMemory', false);
toc
x0 = gather(res(2).x);

tic
conv = convolve_image_cuda(imcv, F1, B1);
toc
x = gather(conv);

fig(1);
sc([x(:, :, 2)]);
fig(2);
sc([x0(:, :, 2)]);
