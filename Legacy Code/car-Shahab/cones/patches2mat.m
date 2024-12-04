function patches2mat(folder, postfix)

if nargin < 2
    postfix = '';    
end

fn = list_files(folder);
info = imfinfo(fn{1});
N = numel(fn);


Xneg = zeros(info.Height * info.Width * 3, N, 'single');
for i = 1:N
    i
    im = imread(fn{i});
    Xneg(:, i) = single(im(:));
end
outfn = sprintf('patches_%d_%d_rgb_%d%s.mat', info.Height, info.Width, ...
                N, postfix);
save(outfn, 'Xneg');
