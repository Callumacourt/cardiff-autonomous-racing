function G = imgallery(im, varargin)

opt.rows = 10;
opt.cols = 20;
opt.gap = 2;
opt = parseargs(opt, varargin{:});

[h, w, d, N] = size(im);

G = zeros(opt.rows * (h + opt.gap) - opt.gap, opt.cols * (w + opt.gap) - opt.gap, d);

count = 1;
posy = 1;
for row = 1:opt.rows
    posx = 1;
    for col = 1:opt.cols
        G(posy:posy + h - 1, posx:posx + w - 1, :) = im(:, :, :, count);
        posx = posx + w + opt.gap;
        count = count + 1;
        if count > N, return; end
    end
    posy = posy + h + opt.gap;
end
