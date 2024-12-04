im = permute(imdb.images.data, [4, 1, 2, 3]);
labels = imdb.images.label(:);

dataset = struct();
dataset.im_train = im(imdb.images.set == 1, :, :);
dataset.im_test = im(imdb.images.set == 2, :, :);
dataset.labels_train = labels(imdb.images.set == 1);
dataset.labels_test = labels(imdb.images.set == 2);

