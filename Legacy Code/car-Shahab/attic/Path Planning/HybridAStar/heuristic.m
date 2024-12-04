function h = heuristic(node)
    global goal_node;
    dx = abs(node.x-goal_node.x);
    dy = abs(node.y-goal_node.y);
    h = sqrt(dx^2 + dy^2);
end