if 0
    fprintf('Loading annotations...\n');
    [imfn, bb] = load_annotated_cones();
    Nbb = sum(cellfun(@numel, bb) / 5);

    cw = 24; ch = 32;
    X = zeros(cw * ch * 3, Nbb);
    L = zeros(1, Nbb);
    count = 1;
    for i = 1:numel(bb)
        im = imread(imfn{i});
        b = bb{i};
        for j = 1:size(b, 1)
            wnd = im(b(j, 3):b(j, 3)+b(j, 5)-1, b(j, 2):b(j, 2)+b(j, 4)-1, :);
            wnd = imresize(wnd, [32 24]);
            X(:, count) = wnd(:);
            L(count) = b(j, 1);
            count = count + 1;
        end
    end
    % X = X(:, L == 0);
    % L = L(L == 0);
    % [B, ev, avg] = kspca(X);

end

% n = size(Xneg, 2);
% V = permute(reshape(Xneg, 32, 24, 3, n), [1 2 3 4]);
% figure(3); clf;
% sc(V);
