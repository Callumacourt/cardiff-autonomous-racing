function drawCollision(nd)
    [x_coor, y_coor] = corner_points([nd.x, nd.y], rad2deg(nd.theta));
    plotCircle(x_coor(1), y_coor(1), Node.ccr, 'k');
    plotCircle(x_coor(2), y_coor(2), Node.ccr, 'k');
    plotCircle(nd.x, nd.y, Node.cr, 'k');
end