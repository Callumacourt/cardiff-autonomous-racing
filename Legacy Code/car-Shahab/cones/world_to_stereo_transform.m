function [Rl, Tl, Rr, Tr] = world_to_stereo_transform(stereoParams, rotl, transl, n_l, rotr, transr, n_r)

H_lr = inv([inv(stereoParams.RotationOfCamera2) stereoParams.TranslationOfCamera2'; 0 0 0 1]) * [rotr transr; 0 0 0 1];
rot_lr = H_lr(1:3, 1:3);
trans_lr = H_lr(1:3, 4);
if n_l >= 4 && n_r >= 4
    Rl = rodrigues(0.5 * (rodrigues(rotl) + rodrigues(rot_lr)));
    Tl = 0.5 * (transl + trans_lr);
elseif n_l >= 4 && n_r < 4
    Rl = rotl;
    Tl = transl;
elseif n_l < 4 && n_r >= 4
    Rl = rot_lr;
    Tl = trans_lr;
else
    Rl = [];
    Tl = [];
end

H_lr = ([inv(stereoParams.RotationOfCamera2) stereoParams.TranslationOfCamera2'; 0 0 0 1]) * [rotl transl; 0 0 0 1];
rot_lr = H_lr(1:3, 1:3);
trans_lr = H_lr(1:3, 4);
if n_l >= 4 && n_r >= 4
    Rr = rodrigues(0.5 * (rodrigues(rotr) + rodrigues(rot_lr)));
    Tr = 0.5 * (transr + trans_lr);
elseif n_l >= 4 && n_r < 4
    Rr = rot_lr;
    Tr = trans_lr;
elseif n_l < 4 && n_r >= 4
    Rr = rotr;
    Tr = transr;
else
    Rr = [];
    Tr = [];
end

