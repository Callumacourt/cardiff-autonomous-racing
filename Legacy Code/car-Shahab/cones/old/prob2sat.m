function sg = prob2sat(sg)

t = sort(sg(:));
sg(sg == 0) = t(find(t > 0, 1));
sg = log(sg + 1);
sg = sg ./ max(sg(:));
