function p = pot_segment(x, v1, v2, h, l)

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
a = x2 .* ca - y2 .* sa;

b = xq .* ca - yq .* sa;
c = yq .* ca + xq .* sa;

p = log(b.^2 + c.^2).*((h - l)*b.^2 + 2*a*l*b + (l - h)*c.^2) - ...
    b.*(4*a*l + 3*b*(h - l)) + 4*c.*atan(b./c).*(a*l + b*(h - l));

p = p + log(c.^2 + (a - b).^2).*((l - h)*b.^2 - 2*a*l*b + (h - l)*c.^2 + a*(a*h + a*l)) - ...
    (a - b).*(4*a*l + a*(h - l) + 3*b*(h - l)) + 4*c.*atan((a - b)./c).*(a*l + b*(h - l));
p = p / (4 * a);

ab = (c==0) & ((b==0) | (b==a));
p(ab) = 0;

