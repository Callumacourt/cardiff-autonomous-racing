function [total, layers] = cnn_size(net)

total = 0;
layers = [];
for i = 1:numel(net.layers)
    layer = net.layers{i};
    if ~isempty(layer.weights) && strcmpi(layer.type, 'conv')
        this = numel(layer.weights{1}) + numel(layer.weights{2});
        total = total + this;
        layers(end + 1) = this;
    end    
end
