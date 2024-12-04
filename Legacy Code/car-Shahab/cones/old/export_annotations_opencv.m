opt.negative_folder = '../data/negative/';
opt.labels = [0, 1];
opt.scale = 1.0;
data = prepare_for_cascade_training('labels', opt.labels, 'scale', opt.scale);

fn = dirPlus(opt.negative_folder, ...
    'FileFilter', '\.(jpg|jpeg|png)$', ...
    'ValidateDirFcn', @(x) (isempty(strfind(x.name, 'all'))));

f = fopen('negative.txt', 'w');
for i = 1:numel(fn)
    fprintf(f, '%s\n', GetFullPath(fn{i}));
end
fclose(f);

fprintf('%d negative images.\n', numel(fn));
fprintf('%d images contain positive samples.\n', numel(data));

f = fopen('positive.txt', 'w');
count = 0;
for i = 1:numel(data)
    bb = data(i).objectBoundingBoxes;
    nbb = size(bb, 1);
    fprintf(f, '%s %d', GetFullPath(data(i).imageFilename), ...
        nbb);
    for j = 1:nbb
        fprintf(f, ' %d %d %d %d', bb(j, 1) - 1, bb(j, 2) - 1, bb(j, 3), bb(j, 4));
        if bb(3) <= 0 || bb(4) <= 0
            error('Empty bbox.');
        end
        
        count = count + 1;
    end
    fprintf(f, '\n');
end
fclose(f);
fprintf('%d positive bboxes written.\n', count);
    