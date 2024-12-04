function name = am_name(opt)

label_names = 'ybsr';

name = sprintf('am_%s_vs_bg_%02dx%02d_%.0f', label_names(opt.labels + 1), ...
    opt.ch, opt.cw, opt.energy * 100);
if opt.simplify
    name = [name '_c'];
else
    name = [name '_f'];
end
if opt.colour
    name = [name '_rgb'];
else
    name = [name '_gray'];
end
