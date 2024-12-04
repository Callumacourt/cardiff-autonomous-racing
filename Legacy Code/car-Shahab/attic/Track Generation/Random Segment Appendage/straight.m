function [current_x, current_y, trackLength, failedSegmentCount, segmentTypeArray, centreTrack_xPoints, centreTrack_yPoints] = straight(trackHeading, trackLength, current_x, current_y, straightMinLimit, straightMaxLimit, innerRectangleBoundary, failSafeWhileLoopLimit, failedSegmentCount, segmentTypeArray, centreTrack_xPoints, centreTrack_yPoints)
%-------------------------------------------------------------------------
% Creates straight line for track
%-------------------------------------------------------------------------
usableNewPoint = false;
failSafeWhileLoopCount = 0;
%   Save existing values in case of failure
original_current_x = current_x;
original_current_y = current_y;

while usableNewPoint==false && failSafeWhileLoopCount<failSafeWhileLoopLimit
    failSafeWhileLoopCount
    failSafeWhileLoopCount = failSafeWhileLoopCount + 1;
    straightLength = randi([straightMinLimit straightMaxLimit],1,1);
    new_current_x = current_x + straightLength*sind(trackHeading);
    new_current_y = current_y + straightLength*cosd(trackHeading);
    
    % Segment validity tests
    [usableNewPoint] = rectangle_boundary_checker(usableNewPoint, new_current_x, new_current_y, innerRectangleBoundary);
    % Check that new points don't intersect with previous points
    if usableNewPoint == true
        [subdividedCentreTrack_xPoints,subdividedCentreTrack_yPoints] = subdivide_straight( original_current_x,original_current_y, new_current_x, new_current_y);
        [usableNewPoint] = surrounding_distance_checker(subdividedCentreTrack_xPoints,subdividedCentreTrack_yPoints, centreTrack_xPoints,centreTrack_yPoints);
    end
end
%   Infinite while loop error message
if (failSafeWhileLoopCount==failSafeWhileLoopLimit)
    fprintf('Segment while loop terminated due to reaching failsafe limit of %d loops\n', failSafeWhileLoopLimit);
end

if usableNewPoint == true
    segmentTypeArray = [segmentTypeArray,"Straight"];
    current_x = new_current_x;
    current_y = new_current_y;
    trackLength = trackLength + straightLength;
    % Add x and y coordinate to end of track coordinates
    figure(1); clf;

plot([centreTrack_xPoints ], [centreTrack_yPoints ]);
hold on
plot([centreTrack_xPoints ], [centreTrack_yPoints ], 'r*');

    [centreTrack_xPoints,centreTrack_yPoints] = centre_points(centreTrack_xPoints,centreTrack_yPoints, subdividedCentreTrack_xPoints,subdividedCentreTrack_yPoints);


plot([subdividedCentreTrack_xPoints ], [subdividedCentreTrack_yPoints ], 'g');
plot([subdividedCentreTrack_xPoints ], [subdividedCentreTrack_yPoints ], 'g*');
hold off
xlim([0 300]);
ylim([0 300]);
drawnow;
else
    failedSegmentCount = failedSegmentCount + 1;
    current_x = original_current_x;
    current_y = original_current_y;
end