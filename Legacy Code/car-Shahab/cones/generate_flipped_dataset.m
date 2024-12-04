tic; fprintf('Loading annotations...');
[imfn, bb] = load_annotated_cones('augmented', false);
dt = toc; fprintf('done [%.3f sec]\n', dt);
Nbb = sum(cellfun(@numel, bb) / 5);
fprintf('Found %d annotated cones.\n', Nbb);
N = numel(imfn);

count = 1;
for i = 1:N
    b = bb{i};
    im = imread(imfn{i});
    for j = 1:size(b, 1)
        wnd = im(b(j, 3):b(j, 3)+b(j, 5)-1, b(j, 2):b(j, 2)+b(j, 4)-1, :);
        wndf = fliplr(wnd);
        
        outimfn = sprintf('../data/cones/flipped/%05d.png', count);
        imwrite(wndf, outimfn);
        outlabfn = sprintf('../data/cones/flipped/%05d.txt', count);
        f = fopen(outlabfn, 'w');
        fprintf(f, '%d 1 1 %d %d\n', b(j, 1), size(wndf, 2), size(wndf, 1));
        fclose(f);
        count = count + 1;
    end
end
