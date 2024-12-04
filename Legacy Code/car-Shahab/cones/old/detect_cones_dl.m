


if 0
    load('rcnnStopSigns.mat', 'layers')
    options = trainingOptions('sgdm', ...
        'MiniBatchSize', 32, ...
        'InitialLearnRate', 1e-6, ...
        'MaxEpochs', 30);
    
    
    bboxes = cell(size(gTruth.LabelData, 1), 1);
for i = 1:size(gTruth.LabelData, 1)
    bboxes{i} = [gTruth.LabelData.yellow{i}; gTruth.LabelData.blue{i}; gTruth.LabelData.solid{i}];        
end

% Enlarge
fn = gTruth.DataSource.Source;
scale = 1.3;
min_pad = 6;
for i = 1:numel(bboxes)
    b = bboxes{i};
    ii = imfinfo(fn{i});
    w = ii.Width; h = ii.Height;
    if isempty(b), continue; end
    cx = b(:, 1) + b(:, 3) * 0.5;
    cy = b(:, 2) + b(:, 4) * 0.5;
    
    add_x = max(b(:, 3) * 0.5 * (scale - 1), min_pad);
    add_y = max(b(:, 4) * 0.5 * (scale - 1), min_pad);
    b(:, 1) = b(:, 1) - add_x;
    b(:, 3) = b(:, 3) + 2 * add_x;
    b(:, 2) = b(:, 2) - add_y;
    b(:, 4) = b(:, 4) + 2 * add_y;
    b(:, 1) = max(1, b(:, 1));
    right = b(:, 1) + b(:, 3);
    right = min(right, w);  
    b(:, 3) = right - b(:, 1);

    bot = b(:, 2) + b(:, 4);
    bot = min(bot, h);
    b(:, 4) = bot - b(:, 2);
    bboxes{i} = b;
end



fprintf('Total examples: %d\n', sum(cellfun(@numel, bboxes) / 4));
    empty = cellfun(@isempty, bboxes);
    bboxes(empty) = [];
    % fn = list_files('../data/amz/every100/0*.png');
    fn = gTruth.DataSource.Source;
    fn_test = fn(empty);
    fn(empty) = [];
    
    X = table(fn, bboxes, 'VariableNames', {'imageFilename', 'stopSign'});
    
    rcnn = trainRCNNObjectDetector(X, layers, options, 'NegativeOverlapRange', [0 0.2]);
end

for i = 103:numel(fn_test)
    img = imread(fn_test{i});
    
    tic
    [bbox, score, label] = detect(rcnn, img, 'MiniBatchSize', 128, ...
        'NumStrongestRegions', inf, 'SelectStrongest', true);
    toc
    
    detectedImg = img;
    for j = 1:numel(score)
        if score(j) < 0.9, continue; end;
        b = bbox(j, :);
        aspect = b(3) / b(4);
        if aspect < 0.4 || aspect > 1.25, continue; end
        %     [score, idx] = max(score);
        
        annotation = sprintf('%.4f', score(j));
        
        detectedImg = insertObjectAnnotation(detectedImg, 'rectangle', b, annotation);
    end
    figure(1); clf;
    sc(detectedImg);
end