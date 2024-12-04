fn_2D = list_files('out/stereo/*.jpg');
fn_3D = list_files('out/stereo/*.png');

for i = 1:numel(fn_2D)
    i
    im1 = imread(fn_2D{i});
    im2 = imread(fn_3D{i});
    im2 = imresize(im2, size(im1, 1) / size(im2, 1));
    im = [im1 im2];
    if mod(size(im, 2), 2) ~= 0
        im = [im zeros(size(im, 1), 1, size(im, 3))];
    end
    imwrite(im, sprintf('out/stereo/both_%06d.png', i));
end