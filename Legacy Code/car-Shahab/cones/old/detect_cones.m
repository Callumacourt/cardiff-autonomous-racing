rng('default'); rng(1);

downsample = 1;
min_area = 16 * (downsample^2);

experiment = 'amz';
% experiment = 'amz';
space = 'rgb';
if exist('Pmodel', 'var')
    [fn, ~, gmm, models, template, labels, colour_labels] = load_data(experiment, 'tables', false, 'space', space);
else
    [fn, Pmodel, gmm, models, template, labels, colour_labels] = load_data(experiment, 'tables', true, 'space', space);
end

template = imresize(template, downsample, 'nearest');

if 0
[g, b, r] = meshgrid(0:255, 0:255, 0:255);
pix = uint8([r(:) g(:) b(:)]);
switch lower(space)
    case 'hsv'
        x = rgb2hsv(im2double(pix));
    case 'rgb'
        x = im2double(pix);
end

[idx, D] = knnsearch(models{3}', x);
end
maxD = max(D(:));
Pmodel(:, 3) = 1 - (D(:)' / maxD);

if 0
figure(10); clf;
plot_colour_model(models(1:end-1), gmm(1:end-1), colour_labels(1:end-1, :), 'space', space);
end
colour_labels = [255 255 0; 0 0 255];

figure(1); clf;
DT = [];
figure(2); clf;
for f = 1:numel(fn)
    fprintf('%d/%d\n', f, numel(fn));
    im = imread(fn{f});
    im = imresize(im, downsample, 'nearest');
    [p, n, e] = fileparts(fn{f});
    
    [h, w, d] = size(im);
    if 0
        % SLOW IMPLEMENTATION
        im = label_cones_slow(im, Pgreen, Pyellow, Pblue, Pred, Pasphalt, template, min_area);
    else
        % FAST IMPLEMENTATION
        t = tic;
        tic
        %         [P, C] = prob_cones_fast(im, Pmodel, template);
        P = colour_table_lookup(im, Pmodel);
        
        %         prob_yellow = rescale(reshape(P(1, :), h, w));
        %         prob_yellow = threshold(prob_yellow, 0.98);
        prob_yellow = reshape(P(1, :) < 3, h, w) .* template;
        prob_black = reshape(P(2, :) < 3, h, w) .* template;
        prob_blue = reshape(P(3, :) > 0.9, h, w) .* template;
        prob_white = reshape(P(4, :) < 3, h, w) .* template;
        %         prob_black = threshold(prob_black, 0.98);
        II_yellow = integralImage(prob_yellow);
        II_black = integralImage(prob_black);
        II_blue = integralImage(prob_blue);
        II_white = integralImage(prob_white);
        
%         scale = [81 63 48 39 30 24];
        scale = [30 24 18];
%                         scale = 24;
        AAy = zeros(h, w, numel(scale));
        AAb = zeros(h, w, numel(scale));
        CCy = zeros(size(AAy));
        CCb = zeros(size(AAb));
        count = 1;
        for z = scale
            wh = z;
            ww = round(z / 2);
            
            A = zeros(h, w);
            
            i = 1:h - wh + 1;
            j = 1:w - ww + 1;        %                 II(i + wh, j + ww, :) + II(i, j, :) - II(i, j + ww, :) - II(i + wh, j, :);
            %             tic
            top = II_yellow(i + wh / 3 - 1, j + ww, :) + II_yellow(i, j, :) - II_yellow(i, j + ww, :) - II_yellow(i + wh / 3 - 1, j, :);
            mid = II_black(i + wh * 2 / 3 - 1, j + ww, :) + II_black(i + wh / 3, j, :) - II_black(i + wh / 3, j + ww, :) - II_black(i + wh * 2 / 3 - 1, j, :);
            bot = II_yellow(i + wh, j + ww, :) + II_yellow(i + wh * 2 / 3, j, :) - II_yellow(i + wh * 2 / 3, j + ww, :) - II_yellow(i + wh, j, :);
            %             toc
            top = top / (wh * ww / 3);
            bot = bot / (wh * ww / 3);
            mid = mid / (wh * ww / 3);
            top = threshold(top, 0.95);
            mid = threshold(mid, 0.95);
            bot = threshold(bot, 0.95);
            %                 top = top ./ max(top(:));
            %         mid = mid ./ max(mid(:));
            %         bot = bot ./ max(bot(:));
            %
            At = A; At(round(i + wh / 2), round(j + ww / 2)) = top;
            Am = A; Am(round(i + wh / 2), round(j + ww / 2)) = mid;
            Ab = A; Ab(round(i + wh / 2), round(j + ww / 2)) = bot;
            A(round(i + wh / 2), round(j + ww / 2)) = top .* mid .* bot;%min(min(top, bot), (1 - mid)); %-(abs(1 - bot) + abs(1 - top) + mid);
            A = A - min(A(:));
            A = A ./ max(A(:));
            AAy(:, :, count) = A;
            
            
               A = zeros(h, w);
            
            i = 1:h - wh + 1;
            j = 1:w - ww + 1;        %                 II(i + wh, j + ww, :) + II(i, j, :) - II(i, j + ww, :) - II(i + wh, j, :);
            %             tic
            top = II_blue(i + wh / 3 - 1, j + ww, :) + II_blue(i, j, :) - II_blue(i, j + ww, :) - II_blue(i + wh / 3 - 1, j, :);
            mid = II_white(i + wh * 2 / 3 - 1, j + ww, :) + II_white(i + wh / 3, j, :) - II_white(i + wh / 3, j + ww, :) - II_white(i + wh * 2 / 3 - 1, j, :);
            bot = II_blue(i + wh, j + ww, :) + II_blue(i + wh * 2 / 3, j, :) - II_blue(i + wh * 2 / 3, j + ww, :) - II_blue(i + wh, j, :);
            %             toc
            top = top / (wh * ww / 3);
            bot = bot / (wh * ww / 3);
            mid = mid / (wh * ww / 3);
%             top = threshold(top, 0.95);
%             mid = threshold(mid, 0.95);
%             bot = threshold(bot, 0.95);
top = top > 0.3;
mid = mid > 0.3;
bot = bot > 0.3;
            %                 top = top ./ max(top(:));
            %         mid = mid ./ max(mid(:));
            %         bot = bot ./ max(bot(:));
            %
            At = A; At(round(i + wh / 2), round(j + ww / 2)) = top;
            Am = A; Am(round(i + wh / 2), round(j + ww / 2)) = mid;
            Ab = A; Ab(round(i + wh / 2), round(j + ww / 2)) = bot;
            A(round(i + wh / 2), round(j + ww / 2)) = top .* mid .* bot;%min(min(top, bot), (1 - mid)); %-(abs(1 - bot) + abs(1 - top) + mid);
            A = A - min(A(:));
            A = A ./ max(A(:));
            A(isnan(A)) = 0;
            AAb(:, :, count) = A;         
            
            
            count = count + 1;
            
%             a = sort(A(:));
%             th = a(round(numel(a) * 0.9995));
%             tl = a(round(numel(a) * 0.99));
%             thigh = 0.8 * th + 0.2 * tl;
%             tlow = 0.2 * th + 0.8 * tl;
%             c = zeros(size(A));
%             c(A < tlow) = 0;
%             c(A > thigh) = 1;
%             between = A >= tlow & A <= thigh;
%             c(between) = (A(between) - tlow) / (thigh - tlow);
%             CC(:, :, count) = c;
            
        end
        
        %         filt = ones(72, 36);
        %         filt(24:47, :) = 1;
        
        %         c = imfilter(prob, filt);
        
        A = (sum(AAy, 3));
        
        %         C(:, 1) = reshape(A > mean(A(:)) + 4 * std(A(:)), [], 1);
        a = sort(A(:));
        %         tzero = a(round(numel(a) * 0.90));
        %         A(A < tzero) = 0;
        
        th = a(round(numel(a) * 0.9995));
        tl = a(round(numel(a) * 0.99));
        
        thigh = 0.8 * th + 0.2 * tl;
        tlow = 0.2 * th + 0.8 * tl;
        %C = A > t;
        %     C = A > mean(A(:)) + 3 * std(A(:));

        c = zeros(size(A));
        c(A < tlow) = 0;
        c(A > thigh) = 1;
        between = A >= tlow & A <= thigh;
        c(between) = (A(between) - tlow) / (thigh - tlow);
        
        C(:, 1) = reshape(c > 0, [], 1);
        
        
          A = (sum(AAb, 3));
        
        %         C(:, 1) = reshape(A > mean(A(:)) + 4 * std(A(:)), [], 1);
        a = sort(A(:));
        %         tzero = a(round(numel(a) * 0.90));
        %         A(A < tzero) = 0;
        
%         th = a(round(numel(a) * 0.9995));
%         tl = a(round(numel(a) * 0.99));
%         
%         thigh = 0.8 * th + 0.2 * tl;
%         tlow = 0.2 * th + 0.8 * tl;
%         %C = A > t;
%         %     C = A > mean(A(:)) + 3 * std(A(:));
%         c = zeros(size(A));
%         c(A < tlow) = 0;
%         c(A > thigh) = 1;
%         between = A >= tlow & A <= thigh;
%         c(between) = (A(between) - tlow) / (thigh - tlow);
        
c = A > 0;
        C(:, 2) = reshape(c > 0, [], 1);
        
        %                 C(:, 1) = reshape((A > 0.2), [], 1);
        cc = cell(size(C, 2), 1);
        for j = 1:numel(cc)
            cc{j} = bwconncomp(reshape(C(:, j), h, w));
        end
        
                imout = rgb2hsv(im2double(im));
%                 sat = zeros(h, w, size(C, 2));
%                 for j = 1:size(sat, 3)
%                     sat(:, :, j) = prob2sat(reshape(P(j, :), h, w));
%                 end
%         
%                 sat = max(sat, [], 3);
        
                sat = reshape(prob_blue, h, w);
                imout = hsv2rgb(cat(3, imout(:, :, 1), sat .* imout(:, :, 2), imout(:, :, 3)));
        
        set(0, 'CurrentFigure', 2);
        
        
        
%         imout = prob_blue;%reshape(C(:, 1), h, w);
        
        
        ax = gca;
        if isempty(ax.Children)
            sc(imout);
        else
            ax.Children(1).CData = imout;
        end
        
        imwrite(imout, ['out/' experiment '/sat/' n '.jpg']);
        
        
        for j = 1:numel(cc)
            im = display_cones(im, cc{j}, colour_labels(j, :), 0);
        end
        
        DT = [DT; toc(t)];
        
        %         im = sc(cat(3, A, rgb2gray(im)), 'prob');
        imwrite(im, ['out/' experiment '/' n '.jpg']);
        
        
        set(0, 'CurrentFigure', 1);
        ax = gca;
        if isempty(ax.Children)
            sc(im);
        else
            ax.Children(1).CData = im;
        end
        drawnow;
        
        
    end
    
    
    if 0
        
        [im, xg] = display_cones(im, ccg, [0 255 0]);
        [im, xy] = display_cones(im, ccy, [255 255 0]);
        [im, xb] = display_cones(im, ccb, [0 0 255]);
        [im, xr] = display_cones(im, ccr, [255 0 0]);
        
        figure(1); clf; axis ij; grid minor;
        xticks([]);
        yticks([]);
        A = im_homography(im, H);
        %     sc(A);
        
        iH = inv(H);
        hold on
        if ~isempty(xg)
            n = homography_transform(xg, iH);
            plot(n(1, :), n(2, :), 'g*');
        end
        if ~isempty(xy)
            n = homography_transform(xy, iH);
            plot(n(1, :), n(2, :), 'y*');
        end
        if ~isempty(xb)
            n = homography_transform(xb, iH);
            plot(n(1, :), n(2, :), 'b*');
        end
        if ~isempty(xr)
            n = homography_transform(xr, iH);
            plot(n(1, :), n(2, :), 'r*');
        end
        xlim([-3000 3000]);
        ylim([0 1500]);
        hold off
        fig_fn = sprintf('out/2D/%06d.png', i);
        export_fig(fig_fn);
        fig = imread(fig_fn);
        if size(fig, 3) == 1
            fig = cat(3, fig, fig, fig);
        end
        imout = [im2uint8(imresize(A, 0.5)); imresize(imout, 0.5)];
        fig = imresize(fig, [1080 320]);
        imout(1:1080, 1:320, :) = fig;
        [p, n, e] = fileparts(fn{i});
        imwrite(imout, ['out/' n '.jpg']);
    end
end







return;
[h, w, d] = size(im);
temp = im2double(imread('data/cone1.png'));
temp = imresize(temp, 0.5 * 0.5);
[th, tw, td] = size(temp);
temp = temp(:, :, 1) > 0.5;
[trpos, tcpos] = find(temp);
[trneg, tcneg] = find(~temp);

cone_col = [0.4899    0.6580    0.4157]';
T = zeros(h, w);
imr = im(:, :, 1);
img = im(:, :, 2);
imb = im(:, :, 3);
figure(1);
for i = 1:h - th + 1
    i
    for j = 1:1:w - tw + 1
        wndr = im(i:i + th - 1, j:j + tw - 1, 1);
        wndg = im(i:i + th - 1, j:j + tw - 1, 2);
        wndb = im(i:i + th - 1, j:j + tw - 1, 3);
        pos = [wndr(temp) wndg(temp) wndb(temp)]';
        neg = [wndr(~temp) wndg(~temp) wndb(~temp)]';
        dpos = mean(distance(pos, cone_col));
        dneg = mean(distance(neg, cone_col));
        %        D = distance(pos, neg);
        %        d = sum(D(:));
        T(i, j) = dpos - dneg;
    end
    sc(T); drawnow;
end

