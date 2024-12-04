function res = hybrid_astar(grd, om, vis, vis_all, vis_collision)
    global start_node;
    currents_expanded = 0;
    %counter used for dubins path use
    c = 0;
    %maximum additional weight for changing steering angle
    wt = 0.1;
    %weight for how often to check dubins path
    wdb = 1;
    %Configuring starting point
    start_node.g = 0;
    h = Node.d * heuristic(start_node);
    start_node.f = h + start_node.g;
    start_node.n = 1;
    
    open = MinHeap(500);
    open.InsertKey(start_node);
    while open.Count() > 0
        %best current which is the one with lowest f cost found in open list
        current = open.ExtractMin();
        
        currents_expanded = currents_expanded+1;
        if reached_goal(current)
            res = backtrace(current);
            return
        end
        %adding current to closed list
        grd.expandCell(current.x, current.y);

        neighbours = current.getMotionPrimitives();
        expand = Node.empty(numel(neighbours), 0);
        for i = 1:numel(neighbours)
            neighbour = neighbours(i);
            if vis_all
                draw_primitive(current, neighbour, "green");
            end
            %car center right and left point distance
            [c_d, l_d, r_d] = collisionDetection(neighbour, om);
            if c_d > Node.cr && l_d > Node.ccr && r_d > Node.ccr
                if vis_collision
                    drawCollision(neighbour);
                end
                if grd.isInside(neighbour.x, neighbour.y) && ~grd.isExpanded(neighbour.x, neighbour.y)
                    g = current.g+Node.d;
                    %distance plus additional cost penalty for turning
                    %for each change iterval change in steering angle 
                    %0.05 weight is added to the cost 
                    da = current.a - neighbour.a;
                    ga = abs(da/Node.ia*wt);
                    neighbour.g = g;% + ga;
                    h = Node.d * heuristic(neighbour);
                    neighbour.f = g+h;
                    neighbour.parent = current;
                    neighbour.n = current.n+1;
                    %If the current is already in the heap it will replace it
                    open.InsertKeyBeta(neighbour);
                    expand(i) = neighbour;
                    if vis
                        draw_primitive(current, neighbour);
                    end
                end
            end
        end

        for i = 1:numel(expand)
            n = expand(i);
            grd.expandCell(n.x, n.y);
        end
    end
    %no path found
    res = [];
end


