function [inner, outer] = im2cones(T, varargin)

opt.pixel2meters = 1; % One pixel is this many meters
opt.width = 2.0; % Track is this many meters wide
opt = parseargs(opt, varargin{:});

[B, L, N, A] = bwboundaries(T);
if N > 1
    error('More than one component!');
end
outer = B{1}';
inner = B{2}';

decimate = round(5.0 / opt.pixel2meters);
inner = inner(:, 1:decimate:end);
outer = outer(:, 1:decimate:end);
inner = inner * opt.pixel2meters;
outer = outer * opt.pixel2meters;

