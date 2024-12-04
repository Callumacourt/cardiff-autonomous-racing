im = single(imread('../../car_data/cones/amz/every10/000345.png'));
dev = gpuDevice();
net = load('cnn-experiment-cones-np/cones_cnn.mat');
% net.layers{1}.weights{2} = net.layers{1}.weights{2};
net = vl_simplenn_move(net, 'gpu');

im_gpu = gpuArray(im);
tic
res = vl_simplenn(net, im_gpu, [], [], 'ConserveMemory', false);
wait(dev);
toc
x0 = max(0, gather(res(10).x));

% system('./test_cnn.py');
x = load('out.mat'); x = x.res;
x = permute(x, [3, 4, 2, 1]);


figure(1);
sc(x0(:, :, 1));

figure(3);
sc(x(:, :, 1));

% max(max(.max(abs(x - x0))))
