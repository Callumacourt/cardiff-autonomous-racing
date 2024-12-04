fn = list_files('../data/local/amz/*.png');

last = 1;
D = [];
im = imread(fn{last});
for i = 2:numel(fn)
    i
    imn = imread(fn{i});
    fig(1); sc(abs(double(im) - double(imn))); drawnow;
    d = sum(sum(sum(abs(double(im) - double(imn))))) / numel(im);
    D(end + 1) = d;
    fig(2); plot(D); drawnow;
    if d < 0.5
        fprintf('%s is almost identical to %s.\n', fn{i}, fn{last});
        delete(fn{i});
    else
        last = i;
        im = imread(fn{last});
    end
end
