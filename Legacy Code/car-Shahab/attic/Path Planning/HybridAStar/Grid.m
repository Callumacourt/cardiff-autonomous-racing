classdef Grid < handle
    properties 
        width
        height
        %cell grid contains spaced that has been searched by hybrid a*
        cell_grid
    end
    methods
        function obj = Grid(width, height)
            obj.width = width;
            obj.height = height;
            obj.cell_grid = zeros(height, width);
        end
        
        %takes as input a point in [x, y] space
        function res = closestObstacleDistance(obj, p)
            [idx, res] = knnsearch(obj.kdtree, p);
        end
        
        function res = isExpanded(obj, x, y)
            [cx, cy] = obj.discretize(x, y);
            res = obj.cell_grid(cy, cx);
        end
        
        function expandCell(obj, x, y)
            [cx, cy] = obj.discretize(x, y);
            obj.cell_grid(cy, cx) = 1;
        end
        
        function res = isInside(obj, x, y)
            [x, y] = obj.discretize(x, y);
            if (x > 0 && x <= obj.width) && (y > 0 && y <= obj.height)
                res = 1;
            else
                res = 0;
            end
        end
        
        function [cx, cy] = discretize(obj, x, y)
            cx = ceil(x/Node.cs);
            cy = ceil(y/Node.cs);
        end
    end
end
