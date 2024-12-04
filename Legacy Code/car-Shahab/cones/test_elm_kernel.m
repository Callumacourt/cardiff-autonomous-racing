load('elm_training.mat');
data = data(1:3:end, :);
data = elmScale(data')';


c = cvpartition(size(data, 1), 'KFold', 5);
Xtrain = data(c.training(1), :);
Ytrain = lab(c.training(1)) + 1;
train = [Ytrain Xtrain];
clear Xtrain Ytrain
save('elm_train.txt', 'train', '-ascii');

Xtest = data(c.test(1), :);
Ytest = lab(c.test(1)) + 1;
test = [Ytest Xtest];
clear Xtest Ytest
save('elm_test.txt', 'test', '-ascii');

clear data

 [TrainingTime, TestingTime, TrainingAccuracy, TestingAccuracy] = ...
     elm_kernel('elm_train.txt', 'elm_test.txt', 1, 1, 'RBF_kernel', 1)
