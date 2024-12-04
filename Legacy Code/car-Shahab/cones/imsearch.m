needle = imread('~/research/car_data/negative_hard/234384b0cf23d94b3c88b8a2469e1ce5.png');
needle = im2single(needle);
if 0
    negfn = find_negative_images();
end

cone_w = 17; cone_h = 23;
scales = 1.5  .^ -(0:3);
max_C = 0;
for i = 1:numel(negfn)
    im = im2single(imread(negfn{i}));
    [h, w] = size(im);
    for k = 1:numel(scales)
        if scales(k) ~= 1
            imsc = imresize(im, scales(k));
        else
            imsc = im;
        end
        imsc = gpuArray(imsc);
        C = [];
        for c = 1:3
            cc = normxcorr2(needle(:, :, c), imsc(:, :, c));
            if isempty(C)
                C = cc;
            else
                C = C + cc;
            end
        end
        C = gather(C);
        max_C_ = max(C(:));
        if max_C_ > max_C
            max_C = max_C_;
            fprintf('%.4f %s\n', max_C, negfn{i});
            fig(1); clf;
            sc(imsc);
            fig(2); clf;
            sc(C >= max_C - 0.001);
            drawnow;
        end
        
    end
end

