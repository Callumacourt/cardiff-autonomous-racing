function [trackHeading, current_x, current_y, failedSegmentCount, segmentTypeArray, centreTrack_xPoints, centreTrack_yPoints] = constant_radius(trackHeading, current_x, current_y, constantDiameterMinLimit, constantDiameterMaxLimit, innerRectangleBoundary, failSafeWhileLoopLimit, failedSegmentCount, segmentTypeArray, centreTrack_xPoints, centreTrack_yPoints)
%-------------------------------------------------------------------------
% Creates straight line for track
%-------------------------------------------------------------------------
usableNewPoint = false;
failSafeWhileLoopCount = 0;
%   Save existing values in case of failure
original_current_x = current_x;
original_current_y = current_y;
originalTrackHeading = trackHeading;

while usableNewPoint==false && failSafeWhileLoopCount<failSafeWhileLoopLimit
    failSafeWhileLoopCount = failSafeWhileLoopCount + 1;
    radius = randi([constantDiameterMinLimit constantDiameterMaxLimit],1,1)/2;
    %Angle chosen for what a track might likely have to not loop on itself
    sectorAngle = randi([-135 135],1,1);
    new_current_x = current_x + straightLength*sind(trackHeading);
    new_current_y = current_y + straightLength*cosd(trackHeading);
    newTrackHeading = trackHeading + sectorAngle;
    % Segment validity tests
    [usableNewPoint] = rectangle_boundary_checker(usableNewPoint, new_current_x, new_current_y, innerRectangleBoundary);
end

if usableNewPoint == true
    fprintf('Circle radius is %dm and sector angle is %d degrees\n', radius, sectorAngle);
    segmentTypeArray = [segmentTypeArray,"Constant Radius"];
    current_x = new_current_x;
    current_y = new_current_y;
    trackHeading = newTrackHeading;
else
    failedSegmentCount = failedSegmentCount + 1;
    current_x = original_current_x;
    current_y = original_current_y;
    trackHeading = originalTrackHeading;
end