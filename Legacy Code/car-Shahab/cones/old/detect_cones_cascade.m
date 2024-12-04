rng('default'); rng(1);

downsample = 1;
min_area = 16 * (downsample^2);
experiment = 'amz';
% experiment = 'single_lap';

space = 'hsv';
if exist('Pmodel', 'var')
    [fn, ~, gmm, models, template, labels, colour_labels] = load_data(experiment, 'tables', false, 'space', space);
else
    [fn, Pmodel, gmm, models, template, labels, colour_labels] = load_data(experiment, 'tables', true, 'space', space);
end

if 1
figure(10); clf;
plot_colour_model(models(1:end-2), gmm(1:end-2), colour_labels(1:end-2, :), 'space', space);
end

return

det_fn = 'cone_detector.xml';
fprintf('Loading template...\n');

template(1:200, :, :) = 0;
template = imresize(template, downsample, 'nearest');
template = 1 - template;
detector = vision.CascadeObjectDetector(det_fn, 'MaxSize', [64 48] * 1.5, 'MergeThreshold', 3);
%     template = template(271:271+540-1, 481:481+960-1, :);

figure(1); clf;
filt = fspecial('laplacian', 0.5);

test = [25 295 725 1195 1665 1955 2345 2505 2565 2635 2735];
for f = 1:1:1%numel(fn)
    fprintf('%d/%d\n', f, numel(fn));
    im = imread(fn{f});
%     im = im(271:271+540-1, 481:481+960-1, :);
    if downsample ~= 1
        im = imresize(im, downsample, 'nearest');
    end
    imorig = im;
    img = rgb2gray(im);
    
    
    
    im = im2double(im);
        [h, w, d] = size(im);


    
%     pix = im2pix(im);
%     [evec, eval, avg] = kspca(pix);
%     evec = -evec(:, 1);
%     proj = evec' * subcol(pix, avg);
%     proj = rescale(proj);
%     
%     img = reshape(proj, h, w);
    
%     img = imfilter(img, filt);
% [gx, gy] = gradient(img);
% img = sqrt(gx.^2 + gy.^2);
    
%        imout = im2uint8([cat(3, img, img, img); repmat(rgb2gray(im), 1, 1, 3)]);
imout = imorig;

    [p, n, e] = fileparts(fn{f});
    
    tic
    P = colour_table_lookup(imorig, Pmodel);
    d_yellow = max(reshape(P(1, :), h, w), template * 100);
    d_blue = max(reshape(P(3, :), h, w), template * 100);
    
    
    bbox = step(detector, img);
    
    
    
    By = [];
    Bb = [];
    Fy = [];
    Fb = [];
    pad = 6;
    for i = 1:size(bbox, 1)
        b = bbox(i, :);
        b(1) = b(1) + pad; b(3) = b(3) - 2 * pad;
        b(2) = b(2) + pad; b(4) = b(4) - 2 * pad;
        wnd = im(b(2):b(2)+b(4)-1, b(1):b(1)+b(3)-1, :);
        wndy = d_yellow(b(2):b(2)+b(4)-1, b(1):b(1)+b(3)-1);
        wndb = d_blue(b(2):b(2)+b(4)-1, b(1):b(1)+b(3)-1);
        
        %         fig(3); sc([wnd sc(wndy) sc(wndb)]);
        
        dy = nnz(wndy < 3) / numel(wndy);
        db = nnz(wndb < 2) / numel(wndb);
        if dy < 0.1 && db < 0.1
            if dy > db
                Fy = [Fy; b];
            else
                Fb = [Fb; b];
            end
        else
            if dy > db
                By = [By; b];
            else
                Bb = [Bb; b];
            end
        end
        
        %         wnd = im(b(2):b(2)+b(4)-1, b(1):b(1)+b(3)-1, :);
        %         p = im2pix(wnd);
        %         prob = min(mahal(gmm, p'), [], 2);
        %         if mean(prob) < 4
        %             B = [B; b];
        %         else
        %             F = [F; b];
        %         end
    end
    toc
%     if 0
%         %     imout = insertObjectAnnotation(im, 'rectangle', B, 'cone');
%         fig(2); clf;
%         hold on
%         if ~isempty(By)
%             cy = [By(:, 1) + 0.5 * By(:, 3) By(:, 2) + 0.5 * By(:, 4)]';
%             cy = homography_transform(cy, inv(H));
%             plot(cy(1, :), cy(2, :), 'y*');
%             
%         else
%             cy = [];
%         end
%         if ~isempty(Bb)
%             cb = [Bb(:, 1) + 0.5 * Bb(:, 3) Bb(:, 2) + 0.5 * Bb(:, 4)]';
%             cb = homography_transform(cb, inv(H));
%             plot(cb(1, :), cb(2, :), 'b*');detectMultiScale
%             
%         else
%             cb = [];
%         end
%         xlim([-600 1300]);
%         ylim([350 550]);
%         
%         xticks([]); yticks([]);
%         hold off
%         axis ij
%         export_fig('tmp.png');detectMultiScale
%         fg = imread('tmp.png');
%         if size(fg, 3) == 1
%             fg = cat(3, fg, fg, fg);
%         end
%         fg = imresize(fg, [h w]);
%     end
    imout = draw_bbox(imout, By, [255 255 0]);
    imout = draw_bbox(imout, Bb, [0 0 255]);
    imout = draw_bbox(imout, Fy, [128 128 0], 0);
    imout = draw_bbox(imout, Fb, [0 0 128], 0);
    
    
    %     imout = [imout; fg];
%     imout = draw_bbox(imout, F, [255 128 128], 0);
    %         im = sc(cat(3, A, rgb2gray(im)), 'prob');
            imwrite(imout, ['out/' experiment '/' n '.jpg']);
    
    
    set(0, 'CurrentFigure', 1);
    ax = gca;
    if isempty(ax.Children)
        sc(imout);
    else
        ax.Children(1).CData = imout;
    end
    drawnow;
    
    
end
