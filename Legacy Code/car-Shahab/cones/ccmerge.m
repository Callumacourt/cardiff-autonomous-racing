function result = merge_cc(cc)


max_dist = 5;
D = ccdist(cc);
D(D > max_dist) = inf;
A = D > 0 & D < inf;
for i = 1:size(A, 1)
    A(i, i) = 1;
end
G = graph(A);


[bins, sizes] = G.conncomp();
CC = cell(numel(sizes), 1);
for i = 1:numel(CC)
    group = find(bins == i);
    %     coord = [];
    %     for j = 1:numel(group)
    %         [row, col] = ind2sub(cc.ImageSize, cc.PixelIdxList{group(j)});
    %         coord = [coord [col'; row']];
    %     end
    %     CC{i} = coord;
    idx = [];
    for j = 1:numel(group)
        idx = [idx; cc.PixelIdxList{group(j)}];
    end
    CC{i} = idx;
end

result = struct;
result.Connectivity = cc.Connectivity;
result.ImageSize = cc.ImageSize;
result.NumObjects = numel(CC);
result.PixelIdxList = CC;
