function [X, Y] = get_batch(data, batch)

X = data.images.data(:, :, :, batch);
Y = data.images.label(:, :, :, batch);
