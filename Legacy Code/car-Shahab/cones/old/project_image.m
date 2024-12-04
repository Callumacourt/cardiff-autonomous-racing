function T = project_image(im, am)

if ~issingle(im)
    im = single(im);
end
[h, w, d] = size(im);
% tic
T = zeros(am.keep, h * w);
for i = 1:am.keep
    BB = reshape(am.B(:, i), am.ch, am.cw, d);
    avg = reshape(am.avg, am.ch, am.cw, d);
    F = imfilter(im, BB, 'same', 'replicate', 'corr');
    F = (F - avg(:)' * BB(:)) .* am.a(i) + am.b(i);
    T(i, :) = F(:);
end
% toc

% tic
% for i = 1:am.keep
%     BB = reshape(am.B(:, i), am.ch, am.cw, ch);
%     avg = reshape(am.avg, am.ch, am.cw, ch);
%     BBr = BB(:, :, 1);
%     BBg = BB(:, :, 2);
%     BBb = BB(:, :, 3);
%     F = imfilter(imdr, BBr, 'same', 'replicate', 'corr');
%     F = F + imfilter(imdg, BBg, 'same', 'replicate', 'corr');
%     F = F + imfilter(imdb, BBb, 'same', 'replicate', 'corr');
%     F = (F - avg(:)' * BB(:)) .* am.a(i) + am.b(i);
%     T(i, :) = F(:);
% end
% toc
