if 0
    imdb = load('cones_23_17_rgb_padded.mat');
end

im = imdb.images.data(:, :, :, 1000);
[h, s, v] = rgb2hsv(im);

A = im;
fig(1);

for brt = linspace(0.5, 1.5, 5)
for sat = linspace(0.5, 1.5, 5)
    sat
    ns = clamp(s * sat, 0, 1);
    nv = clamp(v * brt, 0, 255);
    a = hsv2rgb(cat(3, h, ns, nv));
    A = cat(4, A, a);
end
end
sc(A)
