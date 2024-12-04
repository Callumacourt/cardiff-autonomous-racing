function E = efield_segment(x, v1, v2)

x1 = v1(1);
y1 = v1(2);
x2 = v2(1);
y2 = v2(2);

% Translate so that x1 = 0, y1 = 0
x2 = x2 - x1;
y2 = y2 - y1;
xq = x(1, :) - x1;
yq = x(2, :) - y1;

alpha = -atan2(y2, x2);

ca = cos(alpha);
sa = sin(alpha);
l = x2 .* ca - y2 .* sa;

a = xq .* ca - yq .* sa;
b = yq .* ca + xq .* sa;

a2b2 = a.^2 + b.^2;

Ex0 = -log(1 + (-2*a*l + l.^2)./a2b2)/2;

X = a ./ b;
Y = X - l ./ b;

Ey0 = atan(X) - atan(Y);

Ex = Ex0 .* ca + Ey0 .* sa;
Ey = Ey0 .* ca - Ex0 .* sa;

E = [Ex; Ey];

