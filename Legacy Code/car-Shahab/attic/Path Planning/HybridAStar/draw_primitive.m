function draw_primitive(n1, n2, c)
    x = [n1.x, n2.x];
    y = [n1.y, n2.y];
    if nargin == 3
        line(x, y, "Color", c);
    else 
        line(x, y);
    end
    pause(0.05)
end
