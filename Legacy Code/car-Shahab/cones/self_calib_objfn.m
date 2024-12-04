function score = self_calib_objfn(y0, y1, x)

Y1 = 0.461;

f = x(1);
alpha = x(2);
H = x(3);


y1 = ((Y1*cos(alpha)^2+H)*f.*y0+(-Y1-2*H)*cos(alpha)*sin(alpha)*f^2)./(Y1*cos(alpha)*sin(alpha).*y0+((-Y1-2*H)*sin(alpha)^2+H)*f);
d = sort(abs(y0 - y1));
d = d(1:ceil(0.9 * numel(d)));

score = mean(d);
