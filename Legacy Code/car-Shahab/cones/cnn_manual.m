if 0
    % imdb = load('cones_24_18_rgb_padded_shifted.mat');
    % imdb = load('cones_24_18_rgb_padded.mat');
    imdb = load('cones_24_18_rgb_padded.mat');
end
net = load('cnn-experiment-cones/cones_cnn.mat');
im = imdb.images.data(:, :, :, 100);

N1 = numel(net.layers{1}.weights{2});
global access
access = zeros(size(im));

out2 = zeros(size(im, 1) / 3, size(im, 2) / 3, N1);
for f = 1:N1
    for row = 1:size(out2, 1)
        for col = 1:size(out2, 2)
            out2(row, col, f) = compute_out2(im, net, row, col, f);
        end
    end
end

N2 = numel(net.layers{4}.weights{2});
out3 = zeros(size(out2, 1), size(out2, 2), N2);
for f = 1:N2
    for row = 1:size(out2, 1)
        for col = 1:size(out2, 2)
            sum = 0.0;
            for df = 1:N1
                for drow = -1:1
                    r = row + drow;
                    for dcol = -1:1
                        c = col + dcol;
                        if r < 1 || c < 1 || r > size(out2, 1) || c > size(out2, 2)
                            pix = 0;
                        else
                            pix = out2(r, c, df);
                        end
                        sum = sum + pix * net.layers{4}.weights{1}(drow + 2, dcol + 2, df, f);
                    end
                end
            end
            sum = sum + net.layers{4}.weights{2}(f);
            out3(row, col, f) = sum;
        end
    end
end

out4 = zeros(size(out3, 1) / 2, size(out3, 2) / 3, N2);
for f = 1:N2
    for row = 1:size(out4, 1)
        for col = 1:size(out4, 2)
            max_val = -10e6;
            for drow = 1:2
                for dcol = 1:3
                    pix = out3((row - 1) * 2 + drow, (col - 1) * 3 + dcol, f);
                    
                    
                    max_val = max(max_val, pix);
                end
            end
            out4(row, col, f) = max(0, max_val);
        end
    end
end


N3 = numel(net.layers{7}.weights{2});
out5 = zeros(N3, 1);
for f = 1:N3
    sum = 0.0;
    for df = 1:8
        for r = 1:4
            for c = 1:2
                pix = out4(r, c, df);
                sum = sum + pix * net.layers{7}.weights{1}(r, c, df, f);
            end
        end
    end
    out5(f) = max(0, sum + net.layers{7}.weights{2}(f));
end

out6 = squeeze(net.layers{9}.weights{1})' * out5 + net.layers{9}.weights{2}'

res = vl_simplenn(net, im, [], [], 'ConserveMemory', true);
response = squeeze(gather(res(end).x))

out6 - response



function val = compute_out2(im, net, row, col, f)
global access
max_val = -10e6;
for drow = 1:3
    for dcol = 1:3
        
        total = 0.0;
%         for ch_conv = 1:3
        for drow_conv = -2:2
            r = (row - 1) * 3 + drow + drow_conv;
            for dcol_conv = -2:2
                c = (col - 1) * 3 + dcol + dcol_conv;
                if r < 1 || c < 1 || r > size(im, 1) || c > size(im, 2)
                    pix = [0; 0; 0];
                else
                    pix = im(r, c, :);
                    pix = pix(:);
                    access(r, c) = access(r, c) + 1;
                end
                total = total + sum(pix .* squeeze(net.layers{1}.weights{1}(drow_conv + 3, dcol_conv + 3, :, f)));
            end
        end
%         end
        
        max_val = max(max_val, total + net.layers{1}.weights{2}(f));
    end
end
val = max(0, max_val);
end
