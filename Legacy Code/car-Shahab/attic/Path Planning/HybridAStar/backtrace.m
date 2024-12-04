%Constructs the path from the node provided to the root node
function path = backtrace(node)
    path = zeros(3, node.n);
    path(1:3, 1) = [node.x;node.y;node.theta];
    for i = 2:node.n
        node = node.parent;
        path(1:3, i) = [node.x;node.y;node.theta];
    end
end