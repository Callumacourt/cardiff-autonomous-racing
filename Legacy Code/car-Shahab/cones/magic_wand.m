function [C, pix] = magic_wand(im, tolerance)

figure(100); clf;

if nargin < 2
    tolerance = 0.15;
end
sc(im);
C = zeros(size(im, 1), size(im, 2));

imout = im;
hsv = rgb2hsv(im);


but   = 0;
ii    = 0;
xlist = [];
ylist = [];
hplot = [];
hold on
Cold = {C};
while but ~= 3
    ii = ii + 1;
    [x, y, but] = ginput(1);
    if but == 1 || but == 2 || but == 26
        if but == 1
            Cold{end + 1} = C;
            C = wand(hsv, round(x), round(y), tolerance);
        end
        if but == 2
            Cold{end + 1} = C;
            C = C | wand(hsv, round(x), round(y), tolerance);
        end
        if but == 26
            if numel(Cold) > 1
                C = Cold{end};
                Cold = Cold(1:end-1);
            end
        end
        bnd = bwperim(C);
        imout = im;
        imout(:, :, 1) = min(imout(:, :, 1), ~bnd);
        imout(:, :, 2) = max(imout(:, :, 2), bnd);
        imout(:, :, 3) = min(imout(:, :, 3), ~bnd);
        sc(imout);
    end
    idx = find(C);
    pitch = numel(C);
    pix = [im(idx) im(idx + pitch) im(idx + pitch * 2)]';
end
delete(hplot);
hold off
end



function C = wand(im, xlist, ylist, tolerance)

% tolerance = 0.15;

% Check points validity
if isempty(xlist) || isempty(ylist),
    error('Point list is empty');
end

H = size(im, 1); % image height
W = size(im, 2); % image width


k = ylist > 0 & ylist <= H;
k = k & xlist > 0 & xlist <= W;

if ~any(k),
    error('Coordinates out of range');
elseif ~all(k),
    disp('Warning: some coordinates out of range');
end

ylist = ylist(k);
xlist = xlist(k);

N = length(ylist); % Number of reference pixels


%Create the binary mask
color_mask = false(H, W);

if ndims(im) < 3,
    g = double(im);
    for i = 1:N,
        ref = double(im(ylist(i),xlist(i)));
        color_mask = color_mask | (g - ref).^2 <= tolerance^2;
    end
elseif ndims(im) == 3
    c_h = double(im(:, :, 1)); % Red channel
    c_s = double(im(:, :, 2)); % Green channel
    c_v = double(im(:, :, 3)); % Blue channel
    for i = 1:N
        ref_h = double(im(ylist(i), xlist(i), 1));
        ref_s = double(im(ylist(i), xlist(i), 2));
        ref_v = double(im(ylist(i), xlist(i), 3));
        color_mask = color_mask | ...
            ((c_h - ref_h).^2 + (c_s - ref_s).^2 + (c_v - ref_v).^2)...
            <= tolerance^2;
    end
end

% Connected component labelling
[objects, count] = bwlabel(color_mask, 8);


[y x v] = find(objects);
segList = [];

for i = 1:N,
    k = find(x == xlist(i) & y == ylist(i));
    segList = [segList; v(k)];
end

segList = unique(segList);


LUT = zeros(1,count+1);
LUT(segList+1) = 1;
C = LUT(objects+1);
end



% Output
% TAG = 'Binary image result of magicwand';
% obj  = findobj('tag',TAG);

% if true || isempty(obj),
%     h = figure;
%     set(h,'tag',TAG);
%     Name = ['Fig ', num2str(h), ': ', TAG];
%     set(h,'NumberTitle','off','Name',Name);
% else,
%     figure(obj);
% end
