if 1
    fn = list_files('../../car_data/cones/amz/every10/*.png');
%                         fn = list_files('../../car_data/test_days/2019-12-11/recording0/*.jpg');
%         fn = list_files('../../car_data/cones/fsuk19/track1/*.jpg');  
%         fn = list_files('/home/coriolan/research/car_data/cones/office.261019/*.jpg');
%                         fn = list_files('../../car_data/cones/ka-raceing-190819/every10/*.png');
%             fn = list_files('../../car_data/cones/ka-raceing-240919/every10/*.png');
%     fn = list_files('../../car_data/local/amz/*.png');
%     fn = list_files('../../car_data/local/amz-100320/*.png');

% net = load('good_cnns/cnn-experiment-cones-np-23x17-8-8-8-32-4classes/cones_cnn.mat');
% net = load('good_cnns/cnn-experiment-cones-np-23x17-4-6-6-10-4classes-do00-bn/cones_cnn.mat');
% net = load('cnn-experiment-cones-np-23x17-8-8-8-8-4classes-do20/best.mat');     
% net = load('cnn-experiment-cones-np-23x17-4-4-8-12-4classes-do00/best.mat');          
% net = load('cnn-experiment-cones-np-23x17-8-8-8-8-4classes-do00-bn/best.mat');
% net = load('cnn-experiment-cones-np-23x17-6-6-6-8-4classes-do00-bn/best.mat');
% net = load('cnn-experiment-cones-np-23x17-8-4-4-8-4classes-do00-bn/best.mat');
net = load('cnn-experiment-cones-np-23x17-8-6-6-8-4classes-do00-bn/best.mat');

%         net = load('good_cnns/cnn-experiment-cones-np-23x17-8-8-8-16-4classes/cones_cnn.mat');
    try
        net = net.net;
        net.layers(end) = [] ;
        net = cnn_remove_bnorm(net);
        net.layers(find(cellfun(@(x)strcmp(x.type, 'dropout'), net.layers))) = []; %#ok<FNDSB>
    end
    net = vl_simplenn_move(net, 'gpu');
    
end
THR_HARD = 0.8;
scales = 1.5  .^ -(0:3); %linspace(1, 0.125, 4);
% scales = 2 .^ -(0:2);
T = zeros(1, 10);
F = 0;
info = imfinfo(fn{1});
scale = 1;
if info.Height > 600
    scale = 0.5;
end
C = zeros(info.Height * scale, info.Width * scale, 3, 'single', 'gpuArray');
dev = gpuDevice();
channels = [1, 2, 4];
B = [];
for frame = 1:numel(fn)
    im = imread(fn{frame});
    %     img = im2single(rgb2gray(imresize(im, scale))) * 0.5;
    img = imresize(im2single(im), scale);
    
    im = gpuArray(single(im));
    im = imresize(im, scale);
    [h, w, d] = size(im);
    tic
    for k = 1:numel(scales)
        if scales(k) ~= 1
            ims = imresize(im, scales(k));
        else
            ims = im;
        end
        res = vl_simplenn(net, ims, [], [], 'ConserveMemory', false);
%         T = T + [res(:).time];
        F = F + 1;
        res = vl_nnsoftmax(res(end).x);

        
        for channel = 1:numel(channels)
            fg = res(:, :, channels(channel));
            cones = zeros(size(ims, 1), size(ims, 2), 1, 'single', 'gpuArray');
            cones(12:end-11, 9:end-8, :) = fg;
%             bg = cones < 0.95;
%             cones(bg) = 0;
            if scales(k) ~= 1
                cones = imresize(cones, [h, w]);
            end
            if k == 1
                C(:, :, channel) = cones;
            else
                C(:, :, channel) = max(C(:, :, channel), cones);
            end
        end
    end
    wait(dev);
    toc
    
    cones = max(C, [], 3);
    cones(cones < THR_HARD) = 0;
    cones(cones > 0) = 1;
    cc = bwconncomp(gather(cones));
    cc_merged = ccmerge(cc);
    

    
        CC = cell(cc_merged.NumObjects, 1);
        for i = 1:numel(CC)
            [row, col] = ind2sub(size(cones), cc.PixelIdxList{i});
            CC{i} = [col'; row'];
        end
    bboxes = zeros(numel(CC), 4);
    for i = 1:numel(CC)
        bboxes(i, 1) = min(CC{i}(1, :)) - 1;
        bboxes(i, 2) = min(CC{i}(2, :)) - 1;
        bboxes(i, 3) = max(CC{i}(1, :)) - bboxes(i, 1) + 1;
        bboxes(i, 4) = max(CC{i}(2, :)) - bboxes(i, 2) + 1;
    end

    if 0
    Cy = cat(3, C(:, :, 1), C(:, :, 1), zeros(h, w));
    Cb = cat(3, zeros(h, w), zeros(h, w) + 0.4, C(:, :, 2));
    Cr = cat(3, C(:, :, 3), zeros(h, w), zeros(h, w));
    
    C = max(Cy, max(Cb, Cr));
    bg = repmat(max(C, [], 3) < 0.5, [1 1 3]);
    C(bg) = img(bg);
    im_disp = gather(C);
    im_disp = im2uint8(im_disp * 0.5);
    end
    img = rgb2gray(img) * 0.5;
    im_disp = zeros(size(img), 'single', 'gpuArray');
%         # self.cv_image[:, :, 0] = np.maximum(
%         #     self.cv_image_gray, self.detection_cv[:, :, 0])
%         # self.cv_image[:, :, 1] = np.maximum(
%         #     self.cv_image_gray, self.detection_cv[:, :, 0])
%         # self.cv_image[:, :, 2] = np.maximum(
%         #     self.cv_image_gray, self.detection_cv[:, :, 1])
    im_disp(:, :, 1) = max(img, C(:, :, 1));
    im_disp(:, :, 2) = max(img, C(:, :, 1));
    im_disp(:, :, 3) = max(img, C(:, :, 2));
    im_disp = im2uint8(gather(im_disp));
    % C = Cb;
    
    %     C = cat(3, max(img * 0.5, C), max(img * 0.5, C), img * 0.5);
    %     C = C(:, :, [1 2 4]);
    fig(1);
    
    ctr = bbox_centroids(bboxes);
    B = [B ctr];
    im_disp = draw_bbox(im_disp, bboxes, [255 0 0], 1.0);
    if frame == 1
        sc(im_disp);
    else
        f = fig(1);
        f.Children.Children.CData = im_disp;
    end
    drawnow;
    
    
end
