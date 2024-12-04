if 1
    fn = list_files('../../car_data/cones/amz/every10/*.png');
    net = load('cnn-experiment-cones/cones_cnn.mat');
    net = vl_simplenn_move(net, 'gpu');
    
end
im = imread(fn{1});
imcv = matlab2opencv(im);
buf = zeros(24, 18, 3, 'single');
[imh, imw, channels] = size(im);
step = 4;
[cx, cy] = meshgrid(1:step:imw, 1:step:imh);
cone_w = 18; cone_h = 24;
wnd_w = cone_w * 2; wnd_h = cone_h * 2;
x = cx - (wnd_w - 1) * 0.5;
y = cy - (wnd_h - 1) * 0.5;

boxes = [x(:)'; y(:)'; repmat(wnd_w, 1, numel(x)); repmat(wnd_h, 1, numel(y))];
if 1
BUF = zeros(size(buf, 1), size(buf, 2), channels, size(boxes, 2), 'single');

tic
for i = 1:size(BUF, 4)
    getwndnn(buf, im, boxes(1, i), boxes(2, i), boxes(3, i), boxes(4, i));
    BUF(:, :, :, i) = buf;
end
fprintf('Sampling (CPU):   % 4.2f ms\n', toc * 1000);

tic
buf_gpu = gpuArray(BUF);
fprintf('Uploading to GPU: % 4.2f ms\n', toc * 1000);

tic
res = vl_simplenn(net, buf_gpu, [], [], 'ConserveMemory', false);
score = softmax(squeeze(gather(res(end).x)));
fprintf('Evaluation (GPU): % 4.2f ms\n', toc * 1000);
end
% tic
% bufg = getwnd_cuda(imcv, single(boxes));
% fprintf('Sampling (GPU):   % 4.2f ms\n', toc * 1000);
% 
% tic
% res = vl_simplenn(net, bufg, [], [], 'ConserveMemory', true);
% score_gpu = softmax(squeeze(gather(res(end).x)));
% fprintf('Evaluation (GPU): % 4.2f ms\n', toc * 1000);
% 
% max(max(abs(score - score_gpu)))

% fig(1); clf;
% coneness = score_gpu(1, :);
% coneness(coneness < 0.5) = 0;
% coneness = (coneness - 0.5) * 2.0;
% sc(reshape(coneness, imh / step, imw / step));
% fig(2); clf;
% sc(im);
% 
% tic
% b = gather(bufg);
% fprintf('Downloading:      % 4.2f ms\n', toc * 1000);
% max(max(max(max(abs(b - BUF)))))

F1 = single(gather(net.layers{1}.weights{1}));
B1 = single(gather(net.layers{1}.weights{2}));
tic
res_gpu = eval_cnn_cuda(imcv, single(boxes), F1, B1);
toc
x = gather(res_gpu);
x0 = gather(res(4).x);
% 
a = x0(:, :, 1, 20000)
b = x(:, :, 1, 20000)
% a - b
% 
max(max(max(max(abs(x - x0)))))
