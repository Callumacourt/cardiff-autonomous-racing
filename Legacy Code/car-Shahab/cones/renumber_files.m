fn = list_files('../data/local/amz/*.png');

for i = 1:numel(fn)
    [p, n, e] = fileparts(fn{i});
    f = fullfile(p, 'renumbered', [sprintf('%06d', i) e]);
    copyfile(fn{i}, f);
end
