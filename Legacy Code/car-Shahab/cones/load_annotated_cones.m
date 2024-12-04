function [imfn, bb] = load_annotated_cones(varargin)

opt.augmented = true;
opt.minw = 0;
opt.minh = 0;
opt = parseargs(opt, varargin{:});

fn = list_files_recursively('../../car_data/cones', '*.txt');

if ~opt.augmented
    % Ignore artificially augmented images
    ignore = false(numel(fn), 1);
    for i = 1:numel(fn)
        [p, ~, ~] = fileparts(fn{i});
        parts = strsplit(p, '/');
        if strcmpi(parts(end), 'flipped')
            ignore(i) = true;
        end
    end
    fn(ignore) = [];
end

fn = fn';
bb = cell(numel(fn), 1);
imfn = cell(numel(fn), 1);
for i = 1:numel(fn)
    file_name = fn{i};%fullfile(fn(i).folder, fn(i).name);
    bboxes = load(file_name, '-ascii');
    if ~isempty(bboxes)
        ignore = bboxes(:, 4) < opt.minw | bboxes(:, 5) < opt.minh;
        bboxes(ignore, :) = [];
    end
    bb{i} = bboxes;
    
    imfn{i} = replace_ext(file_name, 'png');
    % If there is no corresponding .png image, try .jpg
    if ~(exist(imfn{i}, 'file') == 2)
        imfn{i} = replace_ext(file_name, 'jpg');
    end
end
