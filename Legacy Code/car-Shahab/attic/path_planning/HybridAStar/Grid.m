classdef Grid < handle
    properties 
        width
        height
        cell_size
        %cell_grid is a 3d matrix where the 
        %first layer is used by the hybrid a* algorithm to keep track of
        %traversed terrain
        %second layer is a matrix of track boundaries where 1 is a boundary
        cell_grid
        %cell is another word for node, since a grid is 
        %cells contain cost values (g(node))
        kdtree
    end
    methods
        function obj = Grid(width, height, cell_size, kdtree, boundaries)
            obj.width = width;
            obj.height = height;
            obj.cell_size = cell_size;
            %tree contains co-ordinates of obstacles
            obj.kdtree = kdtree;
            %first z layer represents if the cell has been expanded
            %second z layer represents obsticles/cell_grid boundaries 
            %1 for a boundary
            if nargin == 5
                obj.cell_grid = zeros(height, width, 2);
                obj.cell_grid(:, :, 2) = boundaries;
            elseif nargin == 4 
                obj.cell_grid = zeros(height, width, 2);
            end
            %{
            If using cell grid object > using matrix of numbers
            obj.cell_grid(1) = GridCell(0,0,0);
            for i = 1:width
                for j = 1:height
                    obj.cell_grid(i, j) = GridCell(i, j, 1);
                    %disp(obj.cell_grid(i, j));
                end
            end
            %}
        end
        
        function res = collisionCheck(obj, path)
            for i = 1:size(path, 2)
                x=path(1, i);
                y=path(2, i);
                if ~obj.isTraversable(x, y)
                    res = 0;
                    return
                end
            end
            res = 1;
        end
        
        %takes as input a point in [x, y] space
        function res = closestObstacleDistance(obj, p)
            [idx, res] = knnsearch(obj.kdtree, p);
        end
        
        function res = isTraversable(obj, x, y)
            [cx, cy] = obj.discretize(x, y);
            if obj.isInside(cx, cy) && ~obj.cell_grid(cy, cx, 2) && obj.closestObstacleDistance([x, y]) > Node.cr
                res = 1;
                return
            end
            res = 0;
        end
        
        function res = isExpanded(obj, x, y)
            [cx, cy] = obj.discretize(x, y);
            res = obj.cell_grid(cy, cx, 1);
        end
        
        function setBoundary(obj, x, y)
            obj.cell_grid(x, y, 2) = 1;
        end
        
        function expandCell(obj, x, y)
            [cx, cy] = obj.discretize(x, y);
            obj.cell_grid(cy, cx, 1) = 1;
        end
        
        function plotTrack(obj)
            s = obj.cell_size;
            for i = 1:obj.height
                for j = 1:obj.width
                    if obj.cell_grid(i, j, 2) == 1
                        y = [i-s, i, i, i-s, i-s];
                        x = [j-s, j-s, j, j, j-s];
                        fill(x, y, 'k');
                    end
                end
            end
        end
    end
    methods (Access = private)
        function [cx, cy] = discretize(obj, x, y)
            cx = ceil(x/obj.cell_size);
            cy = ceil(y/obj.cell_size);
        end
        
        function res = isInside(obj, x, y)
            if (x > 0 && x <= obj.width) && (y > 0 && y <= obj.height)
                res = 1;
            else
                res = 0;
            end
        end
    end
end
