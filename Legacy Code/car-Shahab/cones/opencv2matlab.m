function result = opencv2matlab(im)

[h, w, ~] = size(im);
r = im(1:4:end);
g = im(2:4:end);
b = im(3:4:end);
a = im(4:4:end);

result = cat(3, reshape(r, w, h)', reshape(g, w, h)', reshape(b, w, h)', reshape(a, w, h)');