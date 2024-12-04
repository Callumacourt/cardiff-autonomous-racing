function net = cnn_init_id(dim_in, dim_out, varargin)

opt.bnorm = true;
opt.dropout = 5;
opt.design = [10, 10];
opt = parseargs(opt, varargin{:});

design = opt.design;
in = zeros(1, 1, dim_in, 'single');

% rng('default');
% rng(0);

dropout = opt.dropout / 100;

f = 1/100;
net.layers = {};

% BLOCK 1
net.layers{end+1} = struct('type', 'conv', ...
    'weights', {{f * randn(1, 1, dim_in, design(1), 'single'), zeros(1, design(1), 'single')}}, ...
    'stride', 1, ...
    'pad', 0);
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));

net.layers{end+1} = struct('type', 'sigmoid') ;
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));

% BLOCK 2
net.layers{end+1} = struct('type', 'conv', ...
    'weights', {{f*randn(1, 1, design(1), design(2), 'single'), zeros(1, design(2),'single')}}, ...
    'stride', 1, ...
    'pad', 0) ;
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));

net.layers{end+1} = struct('type', 'sigmoid') ;
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));

% OUTPUT
net.layers{end+1} = struct('type', 'conv', ...
    'weights', {{f*randn(1, 1, design(2), dim_out, 'single'),  zeros(1, dim_out, 'single')}}, ...
    'stride', 1, ...
    'pad', 0) ;
net = vl_simplenn_tidy(net); res = vl_simplenn(net, in);
fprintf('in: %d x %d x %d --> out: %d x %d x %d\n', ...
    size(res(end - 1).x, 1), size(res(end - 1).x, 2), size(res(end - 1).x, 3), ...
    size(res(end).x, 1), size(res(end).x, 2), size(res(end).x, 3));

net.layers{end+1} = struct('type', 'pdist');

% net.layers{end+1} = struct('type', 'softmaxloss') ;

if opt.bnorm
    net = insertBnorm(net, 1);
    net = insertBnorm(net, 4);
    net = insertBnorm(net, 7);
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
