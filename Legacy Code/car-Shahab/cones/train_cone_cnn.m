vl_setupnn;
n_classes = 4;

if 0
    imdb = load('cones_23_17_rgb_padded.mat');
    imdb.negim = {};
    for i = 1:numel(imdb.negfn)
        fprintf('%d / %d\n', i, numel(imdb.negfn));
        imdb.negim{i} = imread(imdb.negfn{i});
    end
    if n_classes == 2
        imdb.images.label(imdb.images.label == 2) = 1;
        imdb.images.label(imdb.images.label == 4) = 1;
        imdb.images.label(imdb.images.label == 3) = 2;
    end
end


% 16-8-8-8 [10076 do20], 8-8-8-8 [6988 do20], 6-8-8-12 [7036 do00], 6-8-8-8 [6216 do00] is good -- check hard negatives, retrain, and move to good_cnns
% 6-6-8-8 [5234 do00], 6-6-6-12 [5032 do00] is struggling a little
% 6-6-6-6 [4102 do00] struggling a bit more, probably this is the limit
% Also, neet to retrain 8-8-8-32 in good_cnns with new hard negatives

% With BN:
% 6-6-6-6-bn, 6-4-6-6-bn -- very good
% Try 4-4-6-6?
design = [8, 6, 6, 8];

dropout = 0; % TODO: Try dropout only at some layers
bnorm = true;
    

channels = 3; % size(imdb.images.data, 3)
net = cnn_init_cones_np(n_classes, ...
    size(imdb.images.data, 1), size(imdb.images.data, 2), 3, ...
    'design', design, 'dropout', dropout, 'bnorm', bnorm);

% net = vl_simplenn_move(net, 'gpu') ;

[t, l] = cnn_size(net)
% return

epochs = 1500;
trainOpts.batchSize = 16384;
trainOpts.gpus = 1;
% trainOpts.errorLabels = {'top1err'};
% trainOpts.learningRate = 0.0000256; % Left
trainOpts.learningRate = 0.0000016; %

trainOpts.expDir = sprintf('cnn-experiment-cones-np-%dx%d-%d-%d-%d-%d-%dclasses-do%02d', ...
    size(imdb.images.data, 1), size(imdb.images.data, 2), design(1), design(2), design(3), design(4), ...
    n_classes, dropout);
if bnorm
    trainOpts.expDir = [trainOpts.expDir '-bn'];
end


trainOpts.numEpochs = epochs ;
trainOpts.continue = true ;
if n_classes > 2
    [net, info] = cnn_train(net, imdb, @get_batch_dynamic, trainOpts);
else
    [net, info] = cnn_train(net, imdb, @get_batch_dynamic_binary, trainOpts);
end

net = vl_simplenn_move(net, 'cpu') ;
net.layers(end) = [] ;
net = cnn_remove_bnorm(net);
net.layers(find(cellfun(@(x)strcmp(x.type, 'dropout'), net.layers))) = []; %#ok<FNDSB>

save(fullfile(trainOpts.expDir, 'cones_cnn.mat'), '-struct', 'net') ;



im = 1 * reshape(imdb.images.data, size(imdb.images.data, 1), size(imdb.images.data, 2), channels, []);
tic
res = vl_simplenn(net, im, [], [], 'ConserveMemory', true);
response = squeeze(gather(res(end).x));
toc
[~, pred] = max(response);
1 - (nnz(pred == imdb.images.label) / nnz(pred))

validation = find(imdb.images.set == 2);
1 - (nnz(pred(validation) == imdb.images.label(validation)) / numel(pred(validation)))


conf = confusion(imdb.images.label(validation), pred(validation))

conf = confusion(imdb.images.label, pred)

wrong = find(pred ~= imdb.images.label);
figure(3);
sc(imdb.images.data(:, :, :, wrong));

% fn = imdb.images.label == 1 & pred == 2;
% figure(11);
% sc(imdb.images.data(:, :, :, fn));
%
% fp = imdb.images.label == 2 & pred == 1;
% figure(22);
% sc(imdb.images.data(:, :, :, fp));

if n_classes == 4
    fn = (imdb.images.label == 1 | imdb.images.label == 2 | imdb.images.label == 4) & pred == 3;
    figure(11);
    sc(imdb.images.data(:, :, :, fn));
    
    fp = (imdb.images.label == 3) & (pred == 1 | pred == 2 | pred == 4);
    figure(22);
    sc(imdb.images.data(:, :, :, fp));
else
    fn = (imdb.images.label == 1) & pred == 2;
    figure(11);
    sc(imdb.images.data(:, :, :, fn));
    
    fp = (imdb.images.label == 2) & (pred == 1);
    figure(22);
    sc(imdb.images.data(:, :, :, fp));
end

fn_ = find(fn);
for i = 1:numel(fn_)
    if fn_(i) <= numel(imdb.images.fn)
        fprintf('% 4d: %s\n', i, imdb.images.fn{fn_(i)});
        imdb.images.bb(i, :)
    end
end


