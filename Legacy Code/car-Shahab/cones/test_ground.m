fn = list_files('~/research/car_data/test_days/2019-12-11/recording0_start/*.jpg');
calib = load('../../car_data/test_days/2019-12-11/recording0_calib_flipped/stereoParams.mat');
stereoParams = calib.stereoParams;
P1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0])';
P2 = cameraMatrix(stereoParams.CameraParameters2, ...
    stereoParams.RotationOfCamera2, stereoParams.TranslationOfCamera2)';
cameraMatrix1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0]);
cameraMatrix2 = cameraMatrix(stereoParams.CameraParameters2, eye(3), [0 0 0]);%...

im = imread(fn{1});
[imR_distorted, imL_distorted] = split_stereo_image(im); % WARNING: Flipped!
imL = undistortImage(imL_distorted, stereoParams.CameraParameters1);
imR = undistortImage(imR_distorted, stereoParams.CameraParameters2);

% fig(1); sc(im);
% fig(2); sc([imL imR]);


% Right image
Or = [15; 284] + 1; % Origin
Xr = [399; 299] + 1; % Right axis
Yr = [139; 214] + 1; % Forward axis

% Left image
Ol = [183; 248] + 1; % Origin
Xl = [573; 250] + 1; % Right axis
Yl = [240; 173] + 1; % Forward axis

WO = triangulate_point(Ol, Or, P1, P2);
WX = triangulate_point(Xl, Xr, P1, P2);
WY = triangulate_point(Yl, Yr, P1, P2);

OX = WX - WO; OX = OX ./ vnorm(OX);
OY = WY - WO; OY = OY ./ vnorm(OY);
OZ = cross(OX, OY); OZ = OZ ./ vnorm(OZ);

fprintf('Angle between OX and OY: %.3f deg.\n', rad2deg(acos(dot(OX, OY))));

len = 40 * 4;
WZ = WO + OZ * len;

WOl = project_points(WO, P1);
WXl = project_points(WX, P1);
WYl = project_points(WY, P1);
WZl = project_points(WZ, P1);

WOr = project_points(WO, P2);
WXr = project_points(WX, P2);
WYr = project_points(WY, P2);
WZr = project_points(WZ, P2);

% Project camera origin onto the ground plane
dist = dot(OZ, -WO); % Height of camera over the ground
GO = -dist * OZ; % Origin of the ground coordinate system (in camera coordinates)

F = -WO + [0 0 1]; % Forward vector
GY = [0 0 1] - dot(OZ, F) * OZ;

% Ground coordinate system unit vectors (in camera coordinates)
GOY = GY - GO; GOY = GOY ./ vnorm(GOY);
GOZ = -GO; GOZ = GOZ ./ vnorm(GOZ);
GOX = cross(GOY, GOZ);

GtoC = [GOX(:) GOY(:) GOZ(:) GO(:); 0 0 0 1];

[xx, yy] = meshgrid(-320:40:320, 0:40:1000);
X = [xx(:) yy(:) zeros(size(xx(:)))]';
Xc = rigid(GtoC, X);

projL = project_points(Xc', P1);
projR = project_points(Xc', P2);

fig(1); sc(imL);
hold on
plot([Ol(1) Xl(1)], [Ol(2) Xl(2)], 'r', 'LineWidth', 2);
plot([Ol(1) Yl(1)], [Ol(2) Yl(2)], 'g', 'LineWidth', 2);
% plot([Ol(1) Zl(1)], [Ol(2) Zl(2)], 'b', 'LineWidth', 2);

% Reprojected from the world
plot([WOl(1) WXl(1)], [WOl(2) WXl(2)], 'r--', 'LineWidth', 2);
plot([WOl(1) WYl(1)], [WOl(2) WYl(2)], 'g--', 'LineWidth', 2);
plot([WOl(1) WZl(1)], [WOl(2) WZl(2)], 'b', 'LineWidth', 2);

% Ground
plot(projL(1, :), projL(2, :), 'y*', 'MarkerSize', 8);
hold off

fig(2); sc(imR);
hold on
plot([Or(1) Xr(1)], [Or(2) Xr(2)], 'r', 'LineWidth', 2);
plot([Or(1) Yr(1)], [Or(2) Yr(2)], 'g', 'LineWidth', 2);
% plot([Or(1) Zr(1)], [Or(2) Zr(2)], 'b', 'LineWidth', 2);

% Reprojected from the world
plot([WOr(1) WXr(1)], [WOr(2) WXr(2)], 'r--', 'LineWidth', 2);
plot([WOr(1) WYr(1)], [WOr(2) WYr(2)], 'g--', 'LineWidth', 2);
plot([WOr(1) WZr(1)], [WOr(2) WZr(2)], 'b', 'LineWidth', 2);

% Ground
plot(projR(1, :), projR(2, :), 'y*', 'MarkerSize', 8);
hold off
