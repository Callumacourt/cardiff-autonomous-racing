function conf = confusion(gt, pred)

lab = unique([gt(:); pred(:)]);
N = numel(lab);
conf = zeros(N);
for i = 1:N
    for j = 1:N
        conf(i, j) = nnz(gt == lab(i) & pred == lab(j));
    end
end
% conf(1, 1) = nnz(gt == 0 & pred == 0);
% conf(1, 2) = nnz(gt == 0 & pred == 1);
% conf(2, 1) = nnz(gt == 1 & pred == 0);
% conf(2, 2) = nnz(gt == 1 & pred == 1);
