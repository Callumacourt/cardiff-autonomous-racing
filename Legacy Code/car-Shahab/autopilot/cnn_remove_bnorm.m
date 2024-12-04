function net = cnn_remove_bnorm(net)

net = simpleMergeBatchNorm(net) ;
net = simpleRemoveLayersOfType(net, 'bnorm') ;

% -------------------------------------------------------------------------
function layers = simpleFindLayersOfType(net, type)
% -------------------------------------------------------------------------
layers = find(cellfun(@(x)strcmp(x.type, type), net.layers)) ;

% -------------------------------------------------------------------------
function net = simpleRemoveLayersOfType(net, type)
% -------------------------------------------------------------------------
layers = simpleFindLayersOfType(net, type) ;
net.layers(layers) = [] ;

% -------------------------------------------------------------------------
function net = simpleMergeBatchNorm(net)
% -------------------------------------------------------------------------

for l = 1:numel(net.layers)
  if strcmp(net.layers{l}.type, 'bnorm')
    if ~strcmp(net.layers{l-1}.type, 'conv')
      error('Batch normalization cannot be merged as it is not preceded by a conv layer.') ;
    end
    [filters, biases] = mergeBatchNorm(...
      net.layers{l-1}.weights{1}, ...
      net.layers{l-1}.weights{2}, ...
      net.layers{l}.weights{1}, ...
      net.layers{l}.weights{2}, ...
      net.layers{l}.weights{3}) ;
    net.layers{l-1}.weights = {filters, biases} ;
  end
end

% -------------------------------------------------------------------------
function [filters, biases] = mergeBatchNorm(filters, biases, multipliers, offsets, moments)
% -------------------------------------------------------------------------
% wk / sqrt(sigmak^2 + eps)
% bk - wk muk / sqrt(sigmak^2 + eps)
a = multipliers(:) ./ moments(:,2) ;
b = offsets(:) - moments(:,1) .* a ;
biases(:) = biases(:) + b(:) ;
sz = size(filters) ;
if numel(sz) < 4
    numFilters = 1;
else
numFilters = sz(4) ;
end
filters = reshape(bsxfun(@times, reshape(filters, [], numFilters), a'), sz) ;
