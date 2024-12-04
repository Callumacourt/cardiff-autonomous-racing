function [B, J] = uniquerows(V)
[b, i] = unique(V, 'rows', 'first');
si = sort(i);
B = V(si, :);
[tf, J] = ismember(V, B, 'rows');