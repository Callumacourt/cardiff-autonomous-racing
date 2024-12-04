cam = struct;
P1 = cameraMatrix(stereoParams.CameraParameters1, eye(3), [0 0 0])';
P2 = cameraMatrix(stereoParams.CameraParameters2, ...
    stereoParams.RotationOfCamera2, stereoParams.TranslationOfCamera2)';

cam.P1 = P1;
cam.P2 = P2;
cam.I1 = stereoParams.CameraParameters1.IntrinsicMatrix';
cam.I2 = stereoParams.CameraParameters2.IntrinsicMatrix';
% cam.I1(3, 1) = cam.I1(3, 1) - 0.5;
% cam.I1(3, 2) = cam.I1(3, 2) - 0.5;
% cam.I2(3, 1) = cam.I2(3, 1) - 0.5;
% cam.I2(3, 2) = cam.I2(3, 2) - 0.5;

cam.radial1 = stereoParams.CameraParameters1.Intrinsics.RadialDistortion;
cam.radial2 = stereoParams.CameraParameters2.Intrinsics.RadialDistortion;
cam.tangential1 = stereoParams.CameraParameters1.Intrinsics.TangentialDistortion;
cam.tangential2 = stereoParams.CameraParameters2.Intrinsics.TangentialDistortion;
cam.coeffs1 = [cam.radial1(1:2) cam.tangential1 cam.radial1(3)];
cam.coeffs2 = [cam.radial2(1:2) cam.tangential2 cam.radial2(3)];
cam.GtoC = GtoC;
cam.CtoG = CtoG;
save('cam.mat', '-struct', 'cam');
