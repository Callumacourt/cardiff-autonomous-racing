function [usableNewPoint] = rectangle_boundary_checker(usableNewPoint, new_current_x, new_current_y, innerRectangleBoundary)
%-------------------------------------------------------------------------
% Checks that new x and y coordinate fall within inner rectangle boundary
%-------------------------------------------------------------------------
%usableNewPoint = true;
%return

if new_current_x >= innerRectangleBoundary(1,1) && new_current_x <= innerRectangleBoundary(2,1)
    if new_current_y >= innerRectangleBoundary(1,2) && new_current_y <= innerRectangleBoundary(2,2)
        usableNewPoint = true;
    end
end