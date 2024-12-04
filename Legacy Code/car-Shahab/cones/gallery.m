function gal = gallery(G, h, w, d)

N = size(G, 2);
bbw = w + 2;
bbh = h + 2;
% for i = 1:N
%     im = reshape(G(:, i), h, w);
%     [row, col] = find(im);
%     he = max(row) - min(row) + 1;
%     wi = max(col) - min(col) + 1;
%     bbw = max(wi, bbw);
%     bbh = max(he, bbh);
% end
% bbw = bbw + 16;
% bbh = bbh + 16;
sz = get(groot, 'Screensize');
sw = sz(3);
sh = sz(4);

galrows = ceil(sh * bbw * sqrt(N / (sh * sw * bbw * bbh)));
galcols = ceil(sw * bbh * sqrt(N / (sh * sw * bbw * bbh)));

% galw / bbw = galcols;
% 3/4 * galw / bbh = galrows;
% (galw / bbw) * (3/4 * galw / bbh) = numel(letters);

% galrows = ceil(sqrt(1/2 * (bbw * numel(letters)) / bbh));
% galcols = ceil(sqrt(1/2 * (bbh * numel(letters)) / bbw));
% galcols = sqrt(numel(letters) * 4/3 * (bbw * bbh)) / bbw;
% galrows = ceil(numel(letters) / galcols);
% galcols = ceil(galcols);
count = 1;
gal = zeros(bbh * galrows, bbw * galcols, d);
for r = 1:galrows
    gal((r - 1) * bbh + 1, :) = 0;
    gal(r * bbh, :) = 0;
    for c = 1:galcols
        gal(:, (c - 1) * bbw + 1, :) = 0;
        gal(:, c * bbw, :) = 0;
        im = rescale(reshape(G(:, count), h, w, d));
%         im = (reshape(G(:, count), h, w));
        im(im == 0) = 0.00001;
        [row, col, val] = find(im);
        row = row - min(row) + 1;
        col = col - min(col) + 1;
        top = round((bbh - max(row)) / 2);
        left = round((bbw - max(col)) / 2);
        row = row + top + (r - 1) * bbh;
        col = col + left + (c - 1) * bbw;
        ind = sub2ind(size(gal), row, col);
        gal(ind) = val;
        count = count + 1;
        if count > N, break; end
    end
    if count > N, break; end
end
