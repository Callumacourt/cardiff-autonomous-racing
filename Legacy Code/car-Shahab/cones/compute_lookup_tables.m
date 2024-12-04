function P = compute_lookup_tables(gmm, varargin)

opt.space = 'hsv';
opt = parseargs(opt, varargin{:});

N = numel(gmm);
P = zeros(256^3, N);

[g, b, r] = meshgrid(0:255, 0:255, 0:255);
pix = uint8([r(:) g(:) b(:)]);
switch lower(opt.space)
    case 'hsv'
        x = rgb2hsv(im2double(pix));
    case 'rgb'
        x = im2double(pix);
end
for i = 1:N
    %     P(:, i) = pdf(gmm{i}, hsv);
    P(:, i) = sqrt(min(mahal(gmm{i}, x), [], 2));
end
