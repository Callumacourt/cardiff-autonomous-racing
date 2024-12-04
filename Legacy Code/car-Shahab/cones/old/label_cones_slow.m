function im = label_cones_slow(im, Pgreen, Pyellow, Pblue, Pred, Pasphalt, template, min_area)

[h, w, d] = size(im);
pitch = h * w;
pix = int32([reshape(im(:, :, 1), pitch, []) reshape(im(:, :, 2), pitch, []) reshape(im(:, :, 3), pitch, [])]);


% Green
Pg  = prob_cone(size(im, 1), size(im, 2), template, Pgreen, pix, im);

% Yellow
Py = prob_cone(size(im, 1), size(im, 2), template, Pyellow, pix, im);

% Blue
Pb = prob_cone(size(im, 1), size(im, 2), template, Pblue, pix, im);

% Red
Pr = prob_cone(size(im, 1), size(im, 2), template, Pred, pix, im);

% Asphalt
Pa = prob_cone(size(im, 1), size(im, 2), template, Pasphalt, pix, im);

tg = Pg > Py & Pg > Pb & Pg > Pr & Pg > Pa;
ty = Py > Pg & Py > Pb & Py > Pr & Py > Pa;
tb = Pb > Pg & Pb > Py & Pb > Pr & Pb > Pa;
tr = Pr > Pg & Pr > Py & Pr > Pb & Pr > Pa ;

P = [Pg(:) Py(:) Pb(:) Pr(:) Pa(:)];

[ccg, Cg] = prob2cc(Pg, tg);
[ccy, Cy] = prob2cc(Py, ty);
[ccb, Cb] = prob2cc(Pb, tb);
[ccr, Cr] = prob2cc(Pr, tr);
[im, xg] = display_cones(im, ccg, [0 255 0], min_area);
[im, xy] = display_cones(im, ccy, [255 255 0], min_area);
[im, xb] = display_cones(im, ccb, [0 0 255], min_area);
[im, xr] = display_cones(im, ccr, [255 0 0], min_area);
