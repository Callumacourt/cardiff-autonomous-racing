fn = list_files('out/world_cnn/*');
for i = 1:numel(fn)
    if numel(fn{i}) == 0, continue; end
    [p, n, e] = fileparts(fn{i});
%     p, n, e
    new = fullfile(p, 'renamed', [sprintf('%04d', i) e]);
    copyfile(fn{i}, new);
end
