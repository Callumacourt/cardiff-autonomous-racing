


w = net.layers{1}.weights{1};
asd(w);
w = net.layers{3}.weights{1};
asd(reshape(w, size(w, 1), size(w, 2), 1, []));
w = net.layers{5}.weights{1};
asd(reshape(w, size(w, 1), size(w, 2), 1, []));
w = net.layers{7}.weights{1};
asd(reshape(w, size(w, 1), size(w, 2), 1, []));
w = squeeze(net.layers{9}.weights{1});
asd(w)
