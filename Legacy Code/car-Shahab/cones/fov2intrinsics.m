fov = deg2rad(75); % Horizontal
w = 1280;%960;
h = 720;%540;
f = w / (tan(fov * 0.5) * 2.0);

I = [f 0 0; 0 f 0; w / 2 h / 2 1.0]

trans = [-1200 0 0];
% rot = eye(3);
% pose_ = [rot trans]

P1 = vision.internal.constructCameraMatrix(eye(3), zeros(1, 3), I)';
P2 = vision.internal.constructCameraMatrix(eye(3), trans, I)';


cam.P1 = P1;
cam.P2 = P2;
cam.I1 = I;
cam.I2 = I;

cam.coeffs1 = zeros(1, 5);
cam.coeffs2 = zeros(1, 5);
save('cam.mat', '-struct', 'cam');
