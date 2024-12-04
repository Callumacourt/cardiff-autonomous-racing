if 0
    imdb = load('cones_23_17_rgb_padded.mat');
    net = load('cnn-experiment-cones-np-23x17-6-4-6-6-4classes-do00-bn/cones_cnn.mat');
%     net = net.net;
%     net.layers(end) = [] ;
%     net.layers(find(cellfun(@(x)strcmp(x.type, 'dropout'), net.layers))) = []; %#ok<FNDSB>
    
    %     net = vl_simplenn_move(net, 'gpu');
    
    %     im = 1 * reshape(imdb.images.data, size(imdb.images.data, 1), ...
    %         size(imdb.images.data, 2), size(net.layers{1}.weights{1}, 3), []);
    im = imdb.images.data;
    tic
    res = vl_simplenn(net, im, [], [], 'ConserveMemory', false);
    X = squeeze(gather(res(end-1).x));
    toc
    bg = find(imdb.images.label == 3);
    idx = randperm(numel(bg));
    remove_bg = bg(idx(1:round(numel(idx) * 0.9)));
    X(:, remove_bg) = [];
    ims = imdb.images.data;
    ims(:, :, :, remove_bg) = [];
    imdb.images.label(remove_bg) = [];
%     imdb.images.fn(remove_bg) = [];
end

if 0
    numDims = 2; pcaDims = min(size(net.layers{end}.weights{1}, 4), min(32, size(X, 1)));
    perplexity = 50; theta = .5; alg = 'svd';
    if size(X, 2) < 150, perplexity = round(size(X, 2) / 6); end
    Y = fast_tsne(X', numDims, pcaDims, perplexity, theta, alg);
    Y = Y';
    [U, L, Av] = kspca(Y);
    Y = U * bsxfun(@minus, Y, Av);
end

if 1
    E = imscatter(Y, ims);
    imwrite(E ./ 255, 'cones_cnn_tsne.png');
end

f = figure(1); clf;
hold on
plot(Y(1, imdb.images.label == 1), Y(2, imdb.images.label == 1), 'y.');
plot(Y(1, imdb.images.label == 2), Y(2, imdb.images.label == 2), 'b.');
plot(Y(1, imdb.images.label == 3), Y(2, imdb.images.label == 3), 'w.', 'MarkerSize', 1);
plot(Y(1, imdb.images.label == 4), Y(2, imdb.images.label == 4), 'r.');
hold off

figure(2); clf;


%apply mouse motion function
set(f,'windowbuttonmotionfcn', {@mousemove, Y, ims, imdb.images.fn, imdb.images.bb});

function mousemove(src, ev, Y, ims, fn, bb)

%since this is a figure callback, the first input is the figure handle:
f = src;

%like all callbacks, the second input, ev, isn't used.

%determine which object is below the cursor:
obj=hittest(f); %<-- the important line in this demo

a = f.Children;
point = get(a, 'currentpoint');
x = point(1, 1, 1);
y = point(1, 2, 1);

%     %determine which point we're over:
idx = findclosestpoint2D(x, y, Y);
if idx <= numel(fn)
    fn{idx}
    bb(idx, :)
end
fig(2);
sc(ims(:, :, :, idx));
drawnow;
end


function idx = findclosestpoint2D(x, y, Y)
dist = bsxfun(@minus, Y, [x; y]);
dist = sqrt(sum(dist .^ 2));
[~, idx] = min(dist);
end
