function [im, x] = display_cones(im, cc, colour, min_area, mass)

x = [];
for j = 1:cc.NumObjects
    [row, col] = ind2sub([size(im, 1) size(im, 2)], cc.PixelIdxList{j});
    if numel(row) < min_area, continue; end
    v = minmax(row');
    h = minmax(col');
    aspect = (v(2) - v(1)) / (h(2) - h(1));
%     if aspect < 0.1 || aspect > 1, continue; end
    if nargin < 5
        cx = mean(col); cy = mean(row);
    else
        val = mass(cc.PixelIdxList{j});
        cx = sum(col .* val) / sum(val) ; cy = sum(row .* val) / sum(val);
    end
    
    % For striped cones
    height = (v(2) - v(1));
    v(1) = v(1) - height / 2;
    v(2) = v(2) + height / 2;
    
    x = [x [cx; cy]];
    draw_line_noaa(im, [h(1) v(1); h(1) v(2); h(1) v(1); h(2) v(1)]', ...
        [h(2) v(1); h(2) v(2); h(1) v(2); h(2) v(2)]', colour, 1);
    draw_line_noaa(im, [cx-3 cy; cx cy-3]', [cx+3 cy; cx cy+3]', colour, 1);
end