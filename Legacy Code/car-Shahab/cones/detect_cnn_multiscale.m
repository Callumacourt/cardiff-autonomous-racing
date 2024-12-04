function C = detect_cnn_multiscale(im, net, scale, scales)

[h, w, ~] = size(im);
C = zeros(h, w, 3, 'single', 'gpuArray');
im = gpuArray(single(im));
im = imresize(im, scale);
channels = [1, 2, 4];
% tic
for k = 1:numel(scales)
    new_size = round(size(im) * scales(k));
    if scales(k) ~= 1
        ims = imresize(im, new_size(1:2));
    else
        ims = im;
    end
%     size(ims)
    
    res = vl_simplenn(net, ims, [], [], 'ConserveMemory', false);
    res = vl_nnsoftmax(res(end).x);
    
    
    for channel = 1:numel(channels)
        fg = res(:, :, channels(channel));
        cones = zeros(size(ims, 1), size(ims, 2), 1, 'single', 'gpuArray');
        shift_row = round((size(cones, 1) - size(fg, 1)) * 0.5 + 0.5);
        shift_col = round((size(cones, 2) - size(fg, 2)) * 0.5 + 0.5);
        cones(shift_row+1:shift_row+size(fg, 1), ...
            shift_col+1:shift_col+size(fg, 2), :) = fg;
        %             bg = cones < 0.95;
        %             cones(bg) = 0;
        if scales(k) ~= 1
            cones = imresize(gather(cones), [h, w], 'nearest');
        end
        if k == 1
            C(:, :, channel) = cones;
        else
            C(:, :, channel) = max(C(:, :, channel), cones);
        end
    end
end
% wait(dev);
% toc

