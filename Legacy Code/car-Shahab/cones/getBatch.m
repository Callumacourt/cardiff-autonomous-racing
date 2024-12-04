% --------------------------------------------------------------------
function [im, labels] = getBatch(imdb, batch)
% --------------------------------------------------------------------
im = imdb.images.data(:, :, :, batch);
% im = 1 * reshape(im, size(im, 1), size(im, 2), 1, []) ;
labels = reshape(imdb.images.label(1, batch), 1, 1, 1, []) ;
