data = load('labels_new.mat');
fn = data.fn;
labels = data.labels;

A = [];
for i = 1:numel(fn)
    if isfile(fn{i})
        row = labels(i, :);
        y = row.yellow{:};
        b = row.blue{:};
        s = row.solid{:};
        [p, n, e] = fileparts(fn{i});
        outfn = fullfile(p, [n '.txt']);
        
        if isfile(outfn)
            fprintf('WARNING! %s already exists!\n', outfn);
        end
            y = [zeros(size(y, 1), 1) y];
            b = [ones(size(b, 1), 1) b];
            s = [ones(size(s, 1), 1) * 2 s];
            both = int32([y; b; s]);
            A = [A; both];
            
            if ~isempty(both)
                savemat(both, outfn);
            end
%         end
    else
        fprintf('%s does not exist!\n', fn{i});
    end
end