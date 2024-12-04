load('training_patches.mat');

[mappedX, mapping] = kernel_pca(X', 30);
