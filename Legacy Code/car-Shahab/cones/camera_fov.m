function [fov_x, fov_y] = camera_fov(I)
%CAMERA_FOV    Calculate field of view.
%   [FOV_X, FOV_Y] = CAMERA_FOV(I) computes the fields of view in the
%   horizontal and vertical directions, from camera intrinsics I.

fov_x = rad2deg(2 * atan(I.ImageSize(2) / (2.0 * I.FocalLength(1))));
fov_y = rad2deg(2 * atan(I.ImageSize(1) / (2.0 * I.FocalLength(2))));
