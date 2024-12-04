% net = load('cnn-experiment-cones-np-23x17-16-8-8-8-4classes-do20/best.mat');          
% net = load('cnn-experiment-cones-np-23x17-4-4-6-12-4classes-do00/best.mat');
% net = load('cnn-experiment-cones-np-23x17-8-8-8-8-4classes-do20/best.mat');          
% net = load('cnn-experiment-cones-np-23x17-6-6-6-6-4classes-do00/best.mat');          
net = load('cnn-experiment-cones-np-23x17-6-6-6-6-4classes-do00-bn/best.mat');          

net_large = load('good_cnns/cnn-experiment-cones-np-23x17-8-8-8-16-4classes/cones_cnn.mat');
try
    net = net.net;
    net.layers(end) = [] ;
    net = cnn_remove_bnorm(net);
    net.layers(find(cellfun(@(x)strcmp(x.type, 'dropout'), net.layers))) = []; %#ok<FNDSB>
end
net = vl_simplenn_move(net, 'gpu');
if 0
    imdb = load('cones_23_17_rgb_padded.mat');
    fn = list_files('../../car_data/cones/amz/every10/*.png');
end
im = imdb.images.data(:, :, :, 6501);
% im = single(imread(fn{1}));

net.classes = struct;
net.classes.description = {'y', 'b', 'bg', 'r'};
net_large.classes = struct;
net_large.classes.description = {'y', 'b', 'bg', 'r'};
fig(1);
graphical_deconvolution(net, im, im);
fig(2);
graphical_occlusion(net, im, im, {4, 1});

fig(3);
graphical_deconvolution(net_large, im, im);
fig(4);
graphical_occlusion(net_large, im, im, {4, 1});
