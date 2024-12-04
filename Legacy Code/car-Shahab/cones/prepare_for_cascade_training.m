function data = prepare_for_cascade_training(varargin)

opt.labels = [0, 1];
opt.scale = 1.25;
opt = parseargs(opt, varargin{:});

fprintf('Loading annotations...\n');
[imfn, bb] = load_annotated_cones('augmented', true);
Nbb = sum(cellfun(@numel, bb) / 5);
data = struct;

% Get rid of images without annotations
empty = cellfun(@isempty, bb);
bb(empty) = [];
fn_test = imfn(empty);
imfn(empty) = [];

% Build the bboxes data structure
count = 1;
total = 0;
for i = 1:numel(imfn)
    b = bb{i};
    b = b(ismember(b(:, 1), opt.labels), :);
    if isempty(b), continue; end
    data(count).imageFilename = imfn{i};
    data(count).objectBoundingBoxes = b(:, 2:end);
    total = total + size(b, 1);
    count = count + 1;
end

fprintf('Total examples: %d, of which with relevant labels: %d.\n', Nbb, total);


% Enlarge bboxes
for i = 1:numel(data)
    data(i).objectBoundingBoxes = pad_bbox(data(i).objectBoundingBoxes, ...
        opt.scale);
    
    % Make sure the bounding boxes do not extent past the image
    info = imfinfo(data(i).imageFilename);
    w = info.Width; h = info.Height;
    data(i).objectBoundingBoxes(:, 1) = ...
        max(1, data(i).objectBoundingBoxes(:, 1));
    data(i).objectBoundingBoxes(:, 2) = ...
        max(1, data(i).objectBoundingBoxes(:, 2));
    maxw = w - data(i).objectBoundingBoxes(:, 1) + 1;
    maxh = h - data(i).objectBoundingBoxes(:, 2) + 1;
    data(i).objectBoundingBoxes(:, 3) = min(maxw, data(i).objectBoundingBoxes(:, 3));
    data(i).objectBoundingBoxes(:, 4) = min(maxh, data(i).objectBoundingBoxes(:, 4));
end
