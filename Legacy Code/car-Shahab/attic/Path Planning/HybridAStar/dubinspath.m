function [path, len] = dubinspath(node, r, stepSize)
    global goal_node;
    q0 = [node.x, node.y, node.theta];
    q1 = [goal_node.x, goal_node.y, goal_node.theta];
    [path, len] = dubins(q0,q1,r,stepSize);
    path = [path, [goal_node.x; goal_node.y; goal_node.theta]];
end