path(path, '/home/coriolan/research/lib/mexopencv');
global cameras
w = 640; h = 480;
init_cameras;
% [vidL, vidR, vidTL, vidTR] = load_video2('data/led2/cam0*', 'data/led2/cam1*');
% [vidL, vidR, vidTL, vidTR] = load_video2('data/synth/cam0*', 'data/synth/cam1*');
% close all
% C = load('calib/Calib_Results_stereo_0_1.mat');
Nc = numel(cameras);
% Nc = 2;
[P, K, kc, F, W] = load_calibration('Nc', Nc, 'world', false);


im = cell(Nc, 1);
for i = 1:Nc
    im{i} = cameras{i}.read;
end

nx = 4;
ny = 6;
sx = 22 / 3;
sy = 36.8 / 5;

C = {};
Ccam = [];
for i = 1:Nc
    corners = ksfindcorners(im{i}, 0);
    grid = corners.grid;
    if size(grid, 1) == nx && size(grid, 2) == ny
        % Ok
        C{end + 1} = grid;
        Ccam(end + 1) = i;
    elseif size(grid, 1) == ny && size(grid, 2) == nx
        % Transpose
        C{end + 1} = cat(3, flipud(grid(:, :, 1)'), flipud(grid(:, :, 2)'));
        Ccam(end + 1) = i;
    else
    end
end

for i = 1:Nc
figure(i); clf;
sc(im{i})
hold on
% for i = 1:size(grid, 1)
%     for j = 1:size(grid, 2)
%         x = grid(i, j, 1);
%         y = grid(i, j, 2);
%         
%     end
% end
grid = C{i};
plot(grid(:,:,2), grid(:,:,1),'o');
end
% return

o = zeros(2, numel(C));
x = zeros(2, numel(C));
y = zeros(2, numel(C));
z = zeros(2, numel(C));
for i = 1:numel(C)
    o(:, i) = [C{i}(1, 1, 2); C{i}(1, 1, 1)];
    x(:, i) = [C{i}(end, 1, 2); C{i}(end, 1, 1)];
    y(:, i) = [C{i}(1, end, 2); C{i}(1, end, 1)];
end

O = triangulate(o, K(Ccam), kc(Ccam), P(Ccam));
OX = triangulate(x, K(Ccam), kc(Ccam), P(Ccam));
OY = triangulate(y, K(Ccam), kc(Ccam), P(Ccam));

OX = OX - O;
lenOX = vnorm(OX);
OX = OX ./ lenOX;
OY = OY - O;
lenOY = vnorm(OY);
OY = OY ./ lenOY;
OZ = cross(OX, OY); OZ = OZ ./ vnorm(OZ);
OX = cross(OY, OZ); OX = OX ./ vnorm(OX);

scalex = lenOX / ((nx - 1) * sx);
scaley = lenOY / ((ny - 1) * sy);
scale = 1 / (0.5 * (scalex + scaley));

for i = 1:Nc
    x(:, i) = project(O + OX, K{i}, kc{i}, P{i});
    y(:, i) = project(O + OY, K{i}, kc{i}, P{i});
    z(:, i) = project(O + OZ, K{i}, kc{i}, P{i});
end


% figure(1); clf;
% hdl = imdisp(im);
for i = 1:Nc
    figure(i); clf;
    sc(im{i});
% axes(get(hdl(i), 'Parent'));
hold on
c = C{i};
plot(c(:,:,2), c(:,:,1),'o');
plot([o(1, i) x(1, i)], [o(2, i) x(2, i)], 'g');
plot([o(1, i) y(1, i)], [o(2, i) y(2, i)], 'g');
plot([o(1, i) z(1, i)], [o(2, i) z(2, i)], 'g');
end


[rad2deg(acos(dot(OX, OY))) rad2deg(acos(dot(OY, OZ))) ...
    rad2deg(acos(dot(OZ, OX)))]
RW = [OX OY OZ]';
TW = O;
world.O = O;
world.OX = OY;
world.OY = OX;
world.OZ = OZ;
world.scale = scale * 49.2/50;
save('world.mat', '-struct', 'world');
