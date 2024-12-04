classdef GridCell
    properties
    x 
    y
    %0 non traversable, 1 traversable
    trav
    %0 not traversed, 1 traversed
    expanded
    end
    methods
        function obj = GridCell(x, y, t)
            if nargin > 0
                obj.x = x;
                obj.y = y;
                obj.trav = t;
            else 
                obj.x = 0;
                obj.y = 0;
                obj.trav = 0;
            end
            obj.expanded = 0;
        end
        
        function setExpanded(obj)
            obj.expanded=1;
        end
    end
end