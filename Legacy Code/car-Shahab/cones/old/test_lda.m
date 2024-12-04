pos = load('pos.mat'); pos = pos.proj;
neg = load('neg.mat'); neg = neg.proj_neg;
data = [pos; neg]';
lab = [ones(1, size(pos, 1)) zeros(1, size(neg, 1))];

W = LDA(data', lab');

L = [ones(size(data, 2), 1) data'] * W';
P = exp(L) ./ repmat(sum(exp(L),2),[1 2]);

[~, pred] = max(L, [], 2);
pred = (pred - 1)';
