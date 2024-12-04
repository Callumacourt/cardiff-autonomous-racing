function flip_stereo(fn, outfn)
% fn = '~/research/car_data/test_days/2019-12-11/002000.jpg';
% outfn = '~/research/car_data/test_days/2019-12-11/002000_flipped.jpg';
info = imfinfo(fn);
w = info.Width;
h = info.Height;

outfnL = tempname;
cmd = sprintf('jpegtran -crop %dx%d+0+0 -perfect %s > %s', w/2, h, fn, outfnL);
system(cmd);

outfnR = tempname;
cmd = sprintf('jpegtran -crop %dx%d+%d+0 -perfect %s > %s', w/2, h, w/2, fn, outfnR);
system(cmd);

outfn_expand = tempname;
cmd = sprintf('jpegtran -crop %dx%d+0+0 -perfect -outfile %s %s', w, h, outfn_expand, outfnR);
system(cmd);

cmd = sprintf('jpegtran -drop +%d+0 %s -perfect -outfile %s %s', w/2, outfnL, outfn, outfn_expand);
system(cmd);
delete(outfnL);
delete(outfnR);
delete(outfn_expand);

% im_orig = imread(fn);
% im_f = imread(outfn);
% 
% fig(1); sc(im_orig);
% fig(2); sc(im_f);
