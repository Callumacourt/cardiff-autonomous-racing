function improved_b = align_pairwise(ref, im, b, X, mask, buf)

best_x = [];
best_y = [];
best_w = [];
best_h = [];
min_diff = inf;

ratio = 0.7479;

% Centre of mass
cx = b(1) + (b(3) - 1) * 0.5;
cy = b(2) + (b(4) - 1) * 0.5;

% Enforce proportions keeping the area
% h = sqrt(b(3) * b(4) / ratio);
% w = h * ratio;
w = b(3);
h = b(4);

best_w = w;
best_h = h;

% tic
for dx = [-0.05 -0.025 0 0.025 0.05] * 0.2 * w
    for dy = [-0.05 -0.025 0 0.025 0.05] * 0.2 * h
        x = cx + dx - (w - 1) * 0.5;
        y = cy + dy - (h - 1) * 0.5;
        getwndbl_scale(buf, im, x, y, w, h);
        % fig(1); sc(abs(buf - ref)); drawnow;
        
%         X1 = subcol(X, buf(:));
%         d1 = mean(abs(X1(:)));
        
        d = vec_mad(X, buf, mask);
%         abs(d - d1)
        %d = mean(abs(ref(:) - buf(:)));
        if d < min_diff
            min_diff = d;
            best_x = x;
            best_y = y;
        end
    end
end
% toc
improved_b = [best_x best_y best_w best_h];
