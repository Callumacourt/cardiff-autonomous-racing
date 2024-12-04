rng('default'); rng(1);

experiment = 'amz';
fn = gTruth.DataSource.Source;
bbox = gTruth.LabelData.yellow;

% Asphalt model
cp_asphalt = load_colour_model('models/amz_asphalt.txt');
cp_yellow = load_colour_model('models/amz_cone_yellow.txt');
models = {cp_yellow, cp_asphalt};
gmm = fit_gmms(models, [1, 2]);




Nc = 3;

pix = [];
count = 1;
for j = 1:numel(bbox)
    im = im2double(imread(fn{j}));
    for i = 1:size(bbox{j}, 1)
        b = bbox{j}(i, :);
        wnd = im(b(2):b(2)+b(4)-1, b(1):b(1)+b(3)-1, :);
        
        p = im2pix(wnd);
        phsv = rgb2hsv(p')';
        prob = pdf(gmm{1}, phsv');
        count = count + 1;
        pix = [pix p];
    end
end

hsv = rgb2hsv(pix')';
[cl, model_ctr] = kmeans(hsv(:, :)', Nc, 'replicates', 1);

ctr = [model_ctr];
Nc = size(ctr, 1);

% H = zeros(Nc, Nc, Nd);
H = zeros(Nc, 1);
B = [];
for j = 1:numel(bbox)
    im = im2double(imread(fn{j}));
    for i = 1:size(bbox{j}, 1)
        
        b = bbox{j}(i, :);
        B = [B; b];
        wnd = im(b(2):b(2)+b(4)-1, b(1):b(1)+b(3)-1, :);
        %         [x, y] = meshgrid(1:size(wnd, 1), 1:size(wnd, 2));
        %         coord = [x(:) y(:)]';
        %         D = distance(coord, coord);
        %         D = round((Nd - 1) * D / max(D(:))) + 1;
        
        pix = rgb2hsv(im2pix(wnd)')';
        idx = quantize_pix(pix, ctr');
        
        %         for k1 = 1:size(pix, 2)
        %             for k2 = k1+1:size(pix, 2)
        %                 H(idx(k1), idx(k2), D(k1, k2)) = H(idx(k1), idx(k2), D(k1, k2)) + 1;
        %                 H(idx(k2), idx(k1), D(k1, k2)) = H(idx(k2), idx(k1), D(k1, k2)) + 1;
        %             end
        %         end
        %         [size(wnd, 1), size(wnd, 2)]
        c = accumarray(idx', 1);
        H(1:numel(c)) = H(1:numel(c)) + c;
        
    end
end
H = H / sum(H);

fn = list_files('../data/amz/every100/*.png');
im = im2double(imread(fn{1}));
[h, w, d] = size(im);
B = mean(B);
ww = round(B(3)); wh = round(B(4));
H = repmat(reshape(H, 1, 1, []), h - wh + 1, w - ww + 1, 1);

figure(1);

II = zeros(h + 1, w + 1, Nc);
for f = 1:numel(fn)
    im = imread(fn{f});
    imout = im;
    im = im2double(im);
    
    imq = reshape(quantize_pix(im2pix(rgb2hsv(im)), ctr'), h, w);
    for i = 1:Nc
        II(:, :, i) = integralImage(imq == i);
    end
    
    A = zeros(h, w);
    
    j = 1:w - ww + 1;
    i = 1:h - wh + 1;
    
    c1 = II(i + wh, j + ww, :) + II(i, j, :) - II(i, j + ww, :) - II(i + wh, j, :);
    c1 = bsxfun(@rdivide, c1, sum(c1, 3));
    A(round(i + wh / 2), round(j + ww / 2)) = sum(min(c1, H), 3);%;sum(min(c1, H));
    
        fig(1);
        sc([A]); drawnow;
    
    
    a = sort(A(:));
    th = a(round(numel(a) * 0.9999));
    tl = a(round(numel(a) * 0.995));

    thigh = 0.8 * th + 0.2 * tl;
    tlow = 0.2 * th + 0.8 * tl;
    %C = A > t;
%     C = A > mean(A(:)) + 3 * std(A(:));
C = zeros(size(A));
C(A < tlow) = 0;
C(A > thigh) = 1;
between = A >= tlow & A <= thigh;
C(between) = (A(between) - tlow) / (thigh - tlow);

        fig(2);
        sc(C);
    
        imout = im2uint8(modulate_sat(im, C));
    cc = bwconncomp(C > 0);
    display_cones(imout, cc, [255 255 0], 16, A);
    fig(3); sc(imout);
    drawnow;

    [p, n, e] = fileparts(fn{f});
    imwrite(imout, ['out/' experiment '/' n '.jpg']);
    
end