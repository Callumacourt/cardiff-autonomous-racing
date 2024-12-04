if 1
    negfn = find_negative_images();
end

cone_w = 17; cone_h = 23;
buf = zeros(cone_h, cone_w, 3, 'single');


% net = load('cnn-experiment-cones-np-23x17-6-4-6-6-4classes-do00-bn.19/cones_cnn.mat');
net = load('cnn-experiment-cones-np-23x17-8-6-6-6-4classes-do00-bn/cones_cnn.mat');
net = vl_simplenn_move(net, 'gpu');

scales = 1.5  .^ -(0:3);
for i = 1:numel(negfn)
    im = imread(negfn{i});
    [h, w, d] = size(im);
    imdisp = im * 0.25;
    for k = 1:numel(scales)
        if scales(k) ~= 1
            imsc = imresize(im, scales(k));
        else
            imsc = im;
        end
        ims = gpuArray(single(imsc));
        res = vl_simplenn(net, ims, [], [], 'ConserveMemory', true);
        res = vl_nnsoftmax(res(end).x);
        cones = zeros(size(ims, 1), size(ims, 2), 'single');
        fg = sum(res(:, :, [1, 2, 4]), 3);
        
        cones(12:end-11, 9:end-8, :) = gather(fg);
        cones(cones < 0.5) = 0.0;
        
        fg = cones > 0;
        cc = bwconncomp(fg);
        
        %     r = imdisp(:, :, 1);
        %     r(fg) = 0;
        %     g = imdisp(:, :, 2);
        %     g(fg) = 255;
        %     b = imdisp(:, :, 3);
        %     b(fg) = 0;
        %     imdisp = cat(3, r, g, b);
        %     [p, n, e] = fileparts(negfn{i});
        %     outfn = fullfile('../../car_data/negative_hard_images/', [strrep(strrep(p, '.', ''), '/', '_') '_' n '.png']);
        %     imwrite(imdisp, outfn);
        if cc.NumObjects > 0
            fprintf('%s\n', negfn{i});
        end
        
        for j = 1:cc.NumObjects
            [row, col] = ind2sub(size(cones), cc.PixelIdxList{j});
            row = mean(row);
            col = mean(col);
            x = col - (cone_w - 1) * 0.5;
            y = row - (cone_h - 1) * 0.5;
            getwndnn(buf, imsc, x, y, cone_w, cone_h);
            hash = GetMD5(buf(:));
%                     if strcmpi(hash, '0b6b8dd16218e8c18eaf64f82e5da8ae')
%                         negfn{i}
%                         error('!');
%                     end
            imwrite(buf ./ 255, sprintf('../../car_data/negative_hard/%s.png', hash));
        end
    end
end
