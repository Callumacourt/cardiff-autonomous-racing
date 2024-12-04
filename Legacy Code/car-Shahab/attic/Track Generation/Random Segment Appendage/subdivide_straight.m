function [subdividedCentreTrack_xPoints,subdividedCentreTrack_yPoints] = subdivide_straight( original_current_x,original_current_y, new_current_x, new_current_y)
%-------------------------------------------------------------------------
% Subdividing segment into 1m intervals
%-------------------------------------------------------------------------
distance = sqrt((new_current_y-original_current_y)^2 + (new_current_x-original_current_x)^2);
resolution = 1;
numberOfSegments = ceil(distance / resolution)+1;

subdividedCentreTrack_xPoints = linspace(original_current_x, new_current_x, numberOfSegments);
subdividedCentreTrack_yPoints = linspace(original_current_y, new_current_y, numberOfSegments);

end

