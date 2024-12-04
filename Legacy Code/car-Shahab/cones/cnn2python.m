% net = load('cnn-experiment-cones-np-23x17-8-4-8-6-4classes-do00.1/cones_cnn.mat');
% net = load('cnn-experiment-cones-np/cones_cnn.mat');
% net = load('good_cnns/cnn-experiment-cones-np-23x17-8-8-8-16-4classes/cones_cnn.mat');
net = load('cnn-experiment-cones-np-23x17-8-6-6-6-4classes-do00-bn/cones_cnn.mat');

n = struct();
n.f1 = permute(net.layers{1}.weights{1}, [4, 3, 1, 2]);
w = net.layers{1}.weights{2};
n.b1 = reshape(w, numel(w), 1, 1, 1);

n.f2 = permute(net.layers{3}.weights{1}, [4, 3, 1, 2]);
w = net.layers{3}.weights{2};
n.b2 = reshape(w, numel(w), 1, 1, 1);

n.f3 = permute(net.layers{5}.weights{1}, [4, 3, 1, 2]);
w = net.layers{5}.weights{2};
n.b3 = reshape(w, numel(w), 1, 1, 1);

n.f4 = permute(net.layers{7}.weights{1}, [4, 3, 1, 2]);
w = net.layers{7}.weights{2};
n.b4 = reshape(w, numel(w), 1, 1, 1);

n.f5 = permute(net.layers{9}.weights{1}, [4, 3, 1, 2]);
w = net.layers{9}.weights{2};
n.b5 = reshape(w, numel(w), 1, 1, 1);

save('net-8-6-6-6-4-do00-bn.mat', '-struct', 'n');
    
