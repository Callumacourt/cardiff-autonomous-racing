if 0
    net = load('cnn-experiment-cones/cones_cnn.mat');
    channels = size(net.layers{1}.weights{1}, 3);
    buf = zeros(24, 18, 3, 'single');
    %     net = net.net;
    %     net.layers(end) = [] ;
    %     net.layers(find(cellfun(@(x)strcmp(x.type, 'dropout'), net.layers))) = [];
    
    net = vl_simplenn_move(net, 'gpu');
    fn = list_files('../../car_data/cones/amz/every10/*.png');
end

for i = 1:numel(fn)
    im = imread(fn{i});
    [h, w, d] = size(im);
    im = single(rgb2gray(im));
    im_gpu = gpuArray(im);
    
    res = vl_simplenn(net, im_gpu, [], [], 'ConserveMemory', false);
    c = vl_nnsoftmax(res(end).x);
    c = gather(c);
%     cone = (c(:, :, 1) + c(:, :, 2)) ./ c(:, :, 3);
    cone = imresize(c, [h w]);
    
    fig(1); clf;
    sc(cone);
    drawnow;
end
