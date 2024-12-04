fn = list_files('/home/coriolan/research/cr/cones/fsuk 2019 recordings/track1/*.jpg');

% total = im2double(imread(fn{1}));
% for i = 2:numel(fn)
%     i
%     total = total + im2double(imread(fn{i}));
%     if mod(i, 50) == 0
%         fig(1); sc(total);
%         drawnow;
%     end
% end

h = fspecial('gaussian', [7 7], 10);
avgf = imfilter(avg, h, 'replicate');
% fig(1); sc(avgf);
% fig(2); sc(avg - avgf);
noise = avg - avgf;
% return


fs = [3 3];
for i = 1:numel(fn)
    i
    im = im2double(imread(fn{i})) - noise;
    im(1:270, :, :) = [];
    left = im(:, 1:640, :);
    right = im(:, 641:end, :);
    left = cat(3, imadjust(left(:, :, 1)), imadjust(left(:, :, 2)), imadjust(left(:, :, 3)));
    right = cat(3, imadjust(right(:, :, 1)), imadjust(right(:, :, 2)), imadjust(right(:, :, 3)));
%     im = cat(3, medfilt2(im(:, :, 1), fs), medfilt2(im(:, :, 2), fs), medfilt2(im(:, :, 3), fs));
%     if mod(i, 50) == 0
ima = [left right];
        fig(1); sc(ima);
        drawnow;
%     end

[p, n, e] = fileparts(fn{i});
outfn = fullfile('../data/local/fs2019_track1_fixed/', [n '.png']);
   imwrite(ima, outfn);
end