opt.ch = 23;
opt.cw = 17;
opt.colour = true;
opt.labels = [0, 1];
opt.pad = [];



if 0
    %     [X, L, Xother, fn] = load_positive_patches(opt.labels, 'cw', opt.cw, 'ch', opt.ch, ...
    %         'colour', opt.colour, 'pad', opt.pad);
    %
    %     Xneg = load('patches_24_18_rgb_100000_negative.mat'); Xneg = Xneg.Xneg(:, 1:10:end);
    %
    %     yellow = X(:, L == 0);
    %     blue = X(:, L == 1);
    imdb = load('cones_23_17_rgb_padded.mat');
end
if 0
    [h, w, d, N] = size(imdb.images.data);
    im_yellow = imdb.images.data(:, :, :, imdb.images.label == 1);
    im_blue = imdb.images.data(:, :, :, imdb.images.label == 2);
    im_red = imdb.images.data(:, :, :, imdb.images.label == 4);
    im_bg = imdb.images.data(:, :, :, imdb.images.label == 3);
    yellow = reshape(im_yellow, h * w * d, []);
    blue = reshape(im_blue, h * w * d, []);
    red = reshape(im_red, h * w * d, []);
    bg = reshape(im_bg, h * w * d, []);
    pixy = patches2pixels(yellow);
    pixb = patches2pixels(blue);
    pixr = patches2pixels(red);
    pixn = patches2pixels(bg);
    
    Y = [174; 156; 66];
    B = [42; 63; 98];
    R = [180; 67; 47];
    
    figure(1); clf;
    hold on
    plot3(pixy(1, 1:100:end), pixy(2, 1:100:end), pixy(3, 1:100:end), 'y.');
    plot3(pixb(1, 1:100:end), pixb(2, 1:100:end), pixb(3, 1:100:end), 'b.');
    plot3(pixr(1, 1:100:end), pixr(2, 1:100:end), pixr(3, 1:100:end), 'r.');
    plot3(pixn(1, 1:1000:end), pixn(2, 1:1000:end), pixn(3, 1:1000:end), '.', 'Color', [0.5 0.5 0.5]);
    hold off
    xlabel('r'); ylabel('g'); zlabel('b');
    grid minor
    box on
    whitebg('black');
    
    
    %     return
    
    cones = [pixy pixb pixr];
    X = [cones'; pixn'];
    %     lab = [zeros(size(pixy, 2), 1); zeros(size(pixb, 2), 1) + 1; zeros(size(pixn, 2), 1) + 2];
    lab = [zeros(size(cones, 2), 1); 1 + zeros(size(pixn, 2), 1)];
    [mappedX, mapping] = lda(X, lab, 2);
%     B = mapping.M;
%     avg = mapping.mean(:);
    
    figure(4); clf;
    hold on
    plot(mappedX(lab == 0, 1), mappedX(lab == 0, 2), 'y.');
    %     plot(mappedX(lab == 1, 1), mappedX(lab == 1, 2), 'b.');
    %     plot(mappedX(lab == 1, 1), mappedX(lab == 1, 2), 'b.');
%     plot(mappedX(lab == 1, 1), mappedX(lab == 1, 2), '.', 'Color', [0.5 0.5 0.5]);
    hold off
end


% return

fn = list_files('../../car_data/cones/office.261019/*.jpg');
% fn = list_files('../../car_data/local/amz/*.png');
% fn = list_files('/home/coriolan/research/car_data/cones/fsuk19/track1/*.jpg');
% fn = list_files('/home/coriolan/research/car_data/test_days/2019-12-11/recording0/*.jpg');

% x = [pixy pixb pixn];
% [B, eval, avg] = kspca(x);
% T = B(:, 1:1) * B(:, 1:1)';
% bias = - T * avg + avg;
% T2 = B(:, 2:2) * B(:, 2:2)';
% bias2 = - T2 * avg + avg;
% T3 = B(:, 3:3) * B(:, 3:3)';
% bias3 = - T3 * avg + avg;




frame = 0;
for i = 1:1:numel(fn)
    i
    im = double(imread(fn{i}));
%     im = im_st(:, 1:size(im_st, 2)/2, :);
%     im_orig = im_st(:, 1:size(im_st, 2)/2, :);
    % im = double(imread('/home/coriolan/research/cr/data/single_lap/frame0395.png'));
    [h, w, d] = size(im);
    impix = reshape(im, size(im, 1) * size(im, 2), 3)';
    x = T' * impix;
    x = pinv(T') * x;
    
    % B = B ./ vnorm(B);
    %
    % a = B' * subcol(impix, avg);
    % rec = addcol(B' \ a, avg);
    
    %     proj =  B(:, 1:2)' * subcol(impix, avg);

%     rec = T * impix + bias;
%     rec2 = T2 * impix + bias2;
%     rec3 = T3 * impix + bias3;
%     imrec = [reshape(rec', size(im)) reshape(rec2', size(im));  im_orig reshape(rec3', size(im))];
%     imrec = imresize(imrec, 0.5);

    % With LDA
%     imc = bsxfun(@minus, impix, mapping.mean');
%     proj = imc' * mapping.M;
%     imrec = reshape(proj, h, w);

% dY = -sqrt(sum(bsxfun(@minus, impix, Y) .^ 2));
% dB = -sqrt(sum(bsxfun(@minus, impix, B) .^ 2));
% dR = -sqrt(sum(bsxfun(@minus, impix, R) .^ 2));
% % d = -min(dY, min(dB, dR));
% % imrec = sc(reshape(d, h, w));
% imrec = sc(cat(3, reshape(dY, h, w), reshape(dB, h, w), reshape(dB, h, w)));

imrec = sc(cat(3, reshape(x(1, :), h, w), reshape(x(2, :), h, w), reshape(x(3, :), h, w)));
    
    % max(max(abs(rec - rec_)))
    
%     imwrite(sc(imrec), sprintf('out/lda/%05d.jpg', frame));
    frame = frame + 1;
    
    % fig(2); sc(im);
    fig(3); sc(imrec); drawnow;
end

