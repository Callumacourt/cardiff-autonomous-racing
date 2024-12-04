function idx = findrow(X, row)

% N = size(X, 1);
% idx = 0;
[~, idx] = ismember(row, X, 'rows');
% idx = find(idx, 1);
% for i = 1:N
%     if all(row == X(i, :))
%         idx = i;
%         return;
%     end
% end
% 
