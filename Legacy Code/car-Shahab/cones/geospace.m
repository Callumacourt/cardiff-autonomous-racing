function x = geospace(a, b, n)

c = (b / a) ^ (1 / (n - 1));
c
x = a * c .^ [0:(n - 1)];
