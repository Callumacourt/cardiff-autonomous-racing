%calculates corner points of rectangle at certain angle alpha
function[x_coor, y_coor]= corner_points(center, a)
    l = Node.vlen; 
    w = Node.vwidth;
    c_x=center(1);
    c_y=center(2);
    d = Node.vmaxd;
    beta = rad2deg(atan(w/l));
    %tl tr br bl
    x_theta = [cosd(a+beta),cosd(a-beta),cosd(180+a+beta),cosd(180+a-beta)];
    y_theta = [sind(a+beta),sind(a-beta),sind(180+a+beta),sind(180+a-beta)];
    x_coor = c_x + d*x_theta;
    y_coor = c_y + d*y_theta;
end