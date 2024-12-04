%check node is within the goal radius
function res = reached_goal(node)
    global goal_node;
    global goal_r;
    x = node.x;
    gx = goal_node.x;
    y = node.y;
    gy = goal_node.y;
    res = 0;
    if x > gx - goal_r && x < gx + goal_r
        dy = sqrt(goal_r^2 - (gx-x)^2);
        if y > gy - dy && y < gy + dy
            res = 1;
            return
        end
    end
end