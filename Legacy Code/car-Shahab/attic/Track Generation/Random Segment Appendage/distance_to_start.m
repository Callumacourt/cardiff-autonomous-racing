function [distanceToStart] = distance_to_start(start_x, start_y, current_x, current_y)
%-------------------------------------------------------------------------
% Calculates distance from current point to start point
%-------------------------------------------------------------------------
distanceToStart = sqrt((current_y-start_y)^2 + (current_x-start_x)^2);
end

