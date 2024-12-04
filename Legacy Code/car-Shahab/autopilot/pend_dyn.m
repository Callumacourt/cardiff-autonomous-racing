function dx = pend_dyn(x, F)
F = -F;
M = 1; m = 0.01; b = 0; l = 1; I = 0.006; g = 9.81;
s = sin(x(2)); c = cos(x(2));
dx = [x(3); x(4);
    ((s*x(4)^2*l^3+(c*s*g+F)*l^2)*m^2+((F*M-b*x(3))*l^2+I*s*x(4)^2*l+F*I)*m-I*b*x(3)+F*I*M)/((c^2-1)*l^2*m^2+(-M*l^2-I)*m-I*M);
    ((c*s*x(4)^2*l^2+(s*g+F*c)*l)*m^2+(M*s*g-c*b*x(3)+F*M*c)*l*m)/((c^2-1)*l^2*m^2+(-M*l^2-I)*m-I*M)];
