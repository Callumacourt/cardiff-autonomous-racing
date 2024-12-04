if 1

fn = list_files('../../car_data/test_days/2019-12-11/recording0/*.jpg');
%         fn = list_files('../../car_data/cones/fsuk19/track1/*.jpg');
    %     fn = list_files('/home/coriolan/research/car_data/cones/office.261019/*.jpg');
    net = load('cnn-experiment-cones-np-small/cones_cnn.mat');
%     net = load('cnn-experiment-cones-np/best-val.mat');
%     net = net.net;
%     net = vl_simplenn_move(net, 'cpu') ;
% net.layers(end) = [] ;
% % net = cnn_remove_bnorm(net);
% net.layers(find(cellfun(@(x)strcmp(x.type, 'dropout'), net.layers))) = [];
    net = vl_simplenn_move(net, 'gpu');
    
end
scales = linspace(1, 0.25, 5);
for i = 1:numel(fn)
    im = imread(fn{i});
    [h, w, d] = size(im);
    img = im2double(rgb2gray(im)) * 0.5;
    im = gpuArray(single(im));
    tic
    C = zeros(h, w, 'single');
    for k = 1:numel(scales)
        if scales(k) ~= 1
            ims = imresize(im, scales(k));
        else
            ims = im;
        end
        res = vl_simplenn(net, ims, [], [], 'ConserveMemory', true);
        res = vl_nnsoftmax(res(end).x);
        cones = zeros(size(ims, 1), size(ims, 2), 'single');
        cones(24/2:end-24/2, 18/2:end-18/2) = gather(res(:, :, 1));
        bg = cones < 0.75;
%         cones = (cones - 0.5) * 2.0;
        cones(bg) = 0;
        if scales(k) ~= 1
        cones = imresize(cones, [h, w]);
        end
        C = max(C, cones);
    end
    toc
    
    
    C = cat(3, max(img, C), max(img, C), img);
    
    fig(1);
    if i == 1
        sc(C);
    else
        f = figure(1);
        f.Children.Children.CData = C;
    end
    drawnow;
    
end
