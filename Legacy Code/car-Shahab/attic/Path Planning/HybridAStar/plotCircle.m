function h = plotCircle(x,y,r,c)
    th = 0:pi/50:2*pi;
    xunit = r * cos(th) + x;
    yunit = r * sin(th) + y;
    if nargin == 4
        h = plot(xunit, yunit, 'Color', c);
    else 
        h = plot(xunit, yunit);
    end
end
