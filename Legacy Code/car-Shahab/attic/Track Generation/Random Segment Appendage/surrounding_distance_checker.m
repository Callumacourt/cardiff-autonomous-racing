function [usableNewPoint] = surrounding_distance_checker(subdividedCentreTrack_xPoints,subdividedCentreTrack_yPoints, centreTrack_xPoints,centreTrack_yPoints)
%-------------------------------------------------------------------------
% Checks that new x and y coordinates do not intersect with existing
%-------------------------------------------------------------------------
usableNewPoint = true;

new_points = [subdividedCentreTrack_xPoints; subdividedCentreTrack_yPoints];
old_points = [centreTrack_xPoints; centreTrack_yPoints];

if size(old_points, 2) > 6
    D = distance(new_points, old_points(:, 1:end-6));
    minD = min(D(:));
    if minD < 4
        usableNewPoint = false;
    end
else
   return 
end