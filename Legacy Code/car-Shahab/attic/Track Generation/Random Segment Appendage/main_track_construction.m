%--------------------------------------------------------------------------
% Random Track Generation in accordance to FS-AI 2018 Rules
%--------------------------------------------------------------------------
%   Clear All variables from memory
clear ; clc ; 

%   Track length generation
targetTrackLength = randi([200 500],1,1);
fprintf('Target track length is: %dm\n',targetTrackLength);

%   Track boundary generation for average track
outer_yAxis = targetTrackLength/3; % From hexagon shape (TTL/6 + 2*TTL/6 Sin(30))
outer_xAxis = 2*targetTrackLength*cosd(30)/6;
axisBoundary = 10;
inner_yAxis = round(outer_yAxis)-2*axisBoundary;
inner_xAxis = round(outer_xAxis)-2*axisBoundary;
innerRectangleBoundary = [axisBoundary axisBoundary; axisBoundary+inner_xAxis axisBoundary+inner_yAxis];
fprintf('Outer bounding track rectangle is %dm by %dm\n', round(outer_xAxis), round(outer_yAxis));
fprintf('Inner bounding track rectangle is %dm by %dm\n', round(inner_xAxis), round(inner_yAxis));

%   Initial parameters
trackHeading = 0;
start_x = axisBoundary;
start_y = round(targetTrackLength*sind(30)/6);
fprintf('Starting point of track is: (%d,%d)\n', start_x, start_y);
current_x = start_x;
current_y = start_y;
centreTrack_xPoints = [start_x];
centreTrack_yPoints = [start_y];

%   Counting parameters
trackLength = 0;
[distanceToStart] = distance_to_start(start_x, start_y, current_x, current_y);
failSafeWhileLoopCount = 0;
failedSegmentCount = 0;
failedTrackCount = 0;

%   Parameter limits
failSafeWhileLoopLimit = 100;
straightMinLimit = 7;
straightMaxLimit = 80;
constantDiameterMaxLimit = 47;    % For centreline track
constantDiameterMinLimit = 6;     % For centreline track
trackWidthMinLimit = 3;

%   Array parameter metrics
failedSegmentCountArray = [0];
segmentTypeArray = [];


%   Track construction segment by segment loop

%   Start with a straight
[current_x, current_y, trackLength, failedSegmentCount, segmentTypeArray, centreTrack_xPoints, centreTrack_yPoints] = straight(trackHeading, trackLength, current_x, current_y, round(inner_xAxis/2)-2, round(inner_xAxis/2), innerRectangleBoundary, failSafeWhileLoopLimit, failedSegmentCount, segmentTypeArray, centreTrack_xPoints, centreTrack_yPoints);

%   Determine the remaining segments through random while loop
while true
    failSafeWhileLoopCount = failSafeWhileLoopCount + 1;
    %   Choosing segment type randomly
    segmentType = randi([1 1],1,1);
    switch segmentType
        case 1
            %   Straight
            fprintf('Before function: %d and %d\n', current_x, current_y);
            sectorAngle = randi([-135 135],1,1);
            trackHeading = trackHeading + sectorAngle;
            [current_x, current_y, trackLength, failedSegmentCount, segmentTypeArray, centreTrack_xPoints, centreTrack_yPoints] = straight(trackHeading, trackLength, current_x, current_y, straightMinLimit, straightMaxLimit, innerRectangleBoundary, failSafeWhileLoopLimit, failedSegmentCount, segmentTypeArray, centreTrack_xPoints, centreTrack_yPoints);
            fprintf('After function: %d and %d\n\n', current_x, current_y);
        case 2
            %   Constant Radius Turn
        case 3
            %   Hairpin Turn
    end
    [distanceToStart] = distance_to_start(start_x, start_y, current_x, current_y);
    if (trackLength > 0.9*targetTrackLength && distanceToStart < 50) || failSafeWhileLoopCount > failSafeWhileLoopLimit
        break;
    end
end
%   Infinite while loop error message
if (failSafeWhileLoopCount==failSafeWhileLoopLimit)
    fprintf('Track while loop terminated due to reaching failsafe limit of %d loops\n', failSafeWhileLoopLimit);
end

%   Metrics output
%fprintf('Plot of x coordinates: \n');
%centreTrack_xPoints
%fprintf('Plot of y coordinates: \n');
%centreTrack_yPoints
fprintf('Failed segment count: %d\n', failedSegmentCount);
fprintf('Failed safe while loop count: %d\n', failSafeWhileLoopCount);
%disp(segmentTypeArray);
%fprintf('Number of straight segments: %d\n', sum(segmentTypeArray(:) == "Straight"));
%fprintf('Number of constant radius segments: %d\n', sum(segmentTypeArray(:) == "Constant Radius"));
fprintf('Final distance to start: %d\n', distanceToStart);
fprintf('\nFinal heading angle of track: %d\n', trackHeading);
fprintf('Final length of track: %dm\n', trackLength);
fprintf('Percentage track completion: %d%%\n', round((trackLength/targetTrackLength)*100));

figure(1); clf;

plot([centreTrack_xPoints ], [centreTrack_yPoints ]);
hold on
plot([centreTrack_xPoints ], [centreTrack_yPoints ], 'r*');
hold off
xlim([0 outer_xAxis]);
ylim([0 outer_yAxis]);