function score = objfn_colourspace(y, b, x)

c1 = x(1);
c2 = x(2);
c3 = 1 - c1 - c2;

if c1 < 0 || c2 < 0 || c1 > 1 || c2 > 1 || c3 < 0 || c3 > 1
    score = 1e9;
    return
end

y1 = [c1 c2 c3] * y;
b1 = [c1 c2 c3] * b;

% d = distance(y1(:)', b1(:)');

% score = sum(sum(d));
% x
score = -(abs(mean(y1) - mean(b1)));
