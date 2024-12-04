function im = draw_bbox(im, bbox, colour, alpha)

if nargin < 4
    bold = 1;
end

for i = 1:size(bbox, 1)
    h = [bbox(i, 1) bbox(i, 1) + bbox(i, 3)];
    v = [bbox(i, 2) bbox(i, 2) + bbox(i, 4)];
    draw_line(im, [h(1) v(1); h(1) v(2); h(1) v(1); h(2) v(1)]', ...
        [h(2) v(1); h(2) v(2); h(1) v(2); h(2) v(2)]', colour, alpha);
%     draw_line_noaa(im, [cx-3 cy; cx cy-3]', [cx+3 cy; cx cy+3]', colour, 1);
end
