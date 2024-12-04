fn = 'calibration.261019_opencv.mat';

% cam = stereoParams
cam1 = stereoParams.CameraParameters1;
cam2 = stereoParams.CameraParameters2;

calib = struct();
calib.matrix1 = single(cam1.IntrinsicMatrix);
calib.coeff1 = single([cam1.RadialDistortion(1:2) cam1.TangentialDistortion cam1.RadialDistortion(3)]);
calib.matrix2 = single(cam2.IntrinsicMatrix);
calib.coeff2 = single([cam2.RadialDistortion(1:2) cam2.TangentialDistortion cam2.RadialDistortion(3)]);
% calib = struct(stereoParams);
% calib.CameraParameters1 = struct(stereoParams.CameraParameters1);
% calib.CameraParameters2 = struct(stereoParams.CameraParameters2);
save(fn, '-struct', 'calib', '-v6')