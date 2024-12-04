function [c_d, l_d, r_d] = collisionDetection(node, om)
    [cx, cy] = corner_points([node.x, node.y], node.a);
    r_x = cx(1);
    l_x = cx(2);
    r_y = cy(1);
    l_y = cy(2);
    [idc, c_d] = knnsearch(om, [node.x, node.y]);
    [idl, l_d] = knnsearch(om, [l_x, l_y]);
    [idr, r_d] = knnsearch(om, [r_x, r_y]); 
end