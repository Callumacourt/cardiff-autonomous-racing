function net = cnn_init_cones_np_mono(Nclasses, h, w, dim, varargin)

opt.dropout = 0;
opt.bnorm = false;
opt.design = [8, 4, 6, 8];
opt = parseargs(opt, varargin{:});

design = opt.design;
in = zeros(h, w, 3, 'single');

% rng('default');
% rng(0);

dropout = opt.dropout / 100;

f = 1/100 ;
net.layers = {} ;
% MONO BLOCK

net.layers{end+1} = struct('type', 'conv', ...
    'weights', {{f * randn(1, 1, 3, 2, 'single'), zeros(1, 2, 'single')}}, ...
    'stride', 1, ...
    'pad', 0);
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));



% BLOCK 1
net.layers{end+1} = struct('type', 'conv', ...
    'weights', {{f * randn(7, 5, 2, design(1), 'single'), zeros(1, design(1), 'single')}}, ...
    'stride', 1, ...
    'pad', 0);
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));

if dropout > 0
    net.layers{end+1} = struct('type', 'dropout', 'rate', dropout);
end

net.layers{end+1} = struct('type', 'relu') ;
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));

% BLOCK 2
net.layers{end+1} = struct('type', 'conv', ...
    'weights', {{f*randn(7, 5, design(1), design(2), 'single'), zeros(1, design(2),'single')}}, ...
    'stride', 1, ...
    'pad', 0) ;
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));

% if dropout > 0
%     net.layers{end+1} = struct('type', 'dropout', 'rate', dropout);
% end
net.layers{end+1} = struct('type', 'relu') ;
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));


% BLOCK 3
net.layers{end+1} = struct('type', 'conv', ...
    'weights', {{f * randn(7, 5, design(2), design(3), 'single'), zeros(1, design(3), 'single')}}, ...
    'stride', 1, ...
    'pad', 0) ;
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));

% if dropout > 0
%     net.layers{end+1} = struct('type', 'dropout', 'rate', dropout);
% end

net.layers{end+1} = struct('type', 'relu') ;
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));

% BLOCK 4
net.layers{end+1} = struct('type', 'conv', ...
    'weights', {{f * randn(5, 5, design(3), design(4), 'single'), zeros(1, design(4), 'single')}}, ...
    'stride', 1, ...
    'pad', 0) ;
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));

% if dropout > 0
%     net.layers{end+1} = struct('type', 'dropout', 'rate', dropout);
% end

net.layers{end+1} = struct('type', 'relu') ;
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));


% FC
net.layers{end+1} = struct('type', 'conv', ...
    'weights', {{f*randn(1, 1, design(4), Nclasses, 'single'),  zeros(1, Nclasses, 'single')}}, ...
    'stride', 1, ...
    'pad', 0) ;
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));


net.layers{end+1} = struct('type', 'softmaxloss') ;

if opt.bnorm
    net = insertBnorm(net, 2);
    net = insertBnorm(net, 5);
    net = insertBnorm(net, 8);
    net = insertBnorm(net, 11);
end


net = vl_simplenn_tidy(net);
vl_simplenn_display(net);

% --------------------------------------------------------------------
function net = insertBnorm(net, l)
% --------------------------------------------------------------------
assert(isfield(net.layers{l}, 'weights'));
ndim = size(net.layers{l}.weights{1}, 4);
layer = struct('type', 'bnorm', ...
    'weights', {{ones(ndim, 1, 'single'), zeros(ndim, 1, 'single')}}, ...
    'learningRate', [1 1 0.05], ...
    'weightDecay', [0 0]) ;
net.layers{l}.biases = [] ;
net.layers = horzcat(net.layers(1:l), layer, net.layers(l+1:end)) ;
