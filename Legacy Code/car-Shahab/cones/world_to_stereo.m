function [proj_l, proj_r] = world_to_stereo(X, stereoParams, cameraMatrix1, cameraMatrix2, rotl, transl, n_l, rotr, transr, n_r)

  
H_lr = inv([inv(stereoParams.RotationOfCamera2) stereoParams.TranslationOfCamera2'; 0 0 0 1]) * [rotr transr; 0 0 0 1];
rot_lr = H_lr(1:3, 1:3);
trans_lr = H_lr(1:3, 4);
if n_l >= 4 && n_r >= 4
    rl = rodrigues(0.5 * (rodrigues(rotl) + rodrigues(rot_lr)));
    tl = 0.5 * (transl + trans_lr);
elseif n_l >= 4 && n_r < 4
    rl = rotl;
    tl = transl;
elseif n_l < 4 && n_r >= 4
    rl = rot_lr;
    tl = trans_lr;
else
    rl = [];
    tl = [];
end
if ~isempty(tl)
    proj_l = project_points((rl * X + tl)', cameraMatrix1');
end

H_lr = ([inv(stereoParams.RotationOfCamera2) stereoParams.TranslationOfCamera2'; 0 0 0 1]) * [rotl transl; 0 0 0 1];
rot_lr = H_lr(1:3, 1:3);
trans_lr = H_lr(1:3, 4);
if n_l >= 4 && n_r >= 4
    rl = rodrigues(0.5 * (rodrigues(rotr) + rodrigues(rot_lr)));
    tl = 0.5 * (transr + trans_lr);
elseif n_l >= 4 && n_r < 4
    rl = rot_lr;
    tl = trans_lr;
elseif n_l < 4 && n_r >= 4
    rl = rotr;
    tl = transr;
else
    rl = [];
    tl = [];
end
if ~isempty(tl)
    proj_r = project_points((rl * X + tl)', cameraMatrix2');
end
