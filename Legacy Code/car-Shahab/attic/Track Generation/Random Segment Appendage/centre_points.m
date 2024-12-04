function [centreTrack_xPoints,centreTrack_yPoints] = centre_points(centreTrack_xPoints,centreTrack_yPoints, new_xPoints, new_yPoints)
%-------------------------------------------------------------------------
% Adds new centre points of new segment to existing centre points of track
%-------------------------------------------------------------------------
centreTrack_xPoints = [centreTrack_xPoints new_xPoints];
centreTrack_yPoints = [centreTrack_yPoints new_yPoints];
end

