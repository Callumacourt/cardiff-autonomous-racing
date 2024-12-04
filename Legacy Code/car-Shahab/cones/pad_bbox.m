function bb = pad_bbox(bb, scale)

if isempty(bb), return; end

if scale == 1, return; end
lab = [];
if size(bb, 2) == 5
    lab = bb(:, 1);
    bb = bb(:, 2:end);
end
l = bb(:, 1);
t = bb(:, 2);
w = bb(:, 3);
h = bb(:, 4);

%xx = cx - (ww - 1) * 0.5;
%yy = cy - (hh - 1) * 0.5;
cx = l + (w - 1) * 0.5;
cy = t + (h - 1) * 0.5;
hh = h * scale;
% ww = w * scale;
ww = cone_width_from_height(hh);
xx = cx - (ww - 1) * 0.5;
yy = cy - (hh - 1) * 0.5;

% bb = round([xx yy ww hh]);
bb = [xx yy ww hh];
if ~isempty(lab)
    bb = [lab bb];
end


% if 1
%     scale = 1;
%     min_pad = 6;
%     for i = 1:numel(bboxes)
%         b = bboxes{i};
%         ii = imfinfo(fn{i});
%         w = ii.Width; h = ii.Height;
%         if isempty(b), continue; end
%         cx = b(:, 1) + b(:, 3) * 0.5;
%         cy = b(:, 2) + b(:, 4) * 0.5;
%         
%         add_x = max(b(:, 3) * 0.5 * (scale - 1), min_pad);
%         add_y = max(b(:, 4) * 0.5 * (scale - 1), min_pad);
%         b(:, 1) = b(:, 1) - add_x;
%         b(:, 3) = b(:, 3) + 2 * add_x;
%         b(:, 2) = b(:, 2) - add_y;
%         b(:, 4) = b(:, 4) + 2 * add_y;
%         b(:, 1) = max(1, b(:, 1));
%         right = b(:, 1) + b(:, 3);
%         right = min(right, w);
%         b(:, 3) = right - b(:, 1);
%         
%         bot = b(:, 2) + b(:, 4);
%         bot = min(bot, h);
%         b(:, 4) = bot - b(:, 2);
%         bboxes{i} = b;
%     end
% end
