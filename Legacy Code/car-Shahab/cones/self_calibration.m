bboxes = load('cone_detector/pts.txt');
imw = 960; imh = 540;
px = (imw - 1) * 0.5;
py = (imh - 1) * 0.5;

cx = bboxes(:, 1) + (bboxes(:, 3) - 1) * 0.5;
cy = imh - (bboxes(:, 2) + (bboxes(:, 4) - 1) * 0.5) - 1;

y0 = py - (bboxes(:, 2) - bboxes(:, 4));
y1 = py - bboxes(:, 2);

Y1 = 0.461;

fig(1); clf(1);

plot(cx - px, cy - py, '.');


fig(2); clf(1);
plot(y0, y1, '.');


objfn = @(x) self_calib_objfn(y0, y1, x);

x0 = [0.05, 0.1, 1.3];
options = optimset('Display', 'iter', ...
    'MaxFunEvals', 10000, 'MaxIter', 10000, 'TolX', 1e-9, 'TolFun', 1e-9);

[x, fval] = fminsearch(objfn, x0, options)

