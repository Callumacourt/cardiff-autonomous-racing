if 1
    fprintf('Loading annotations...\n');
    [imfn, bb] = load_annotated_cones('augmented', false, 'minh', 13);
    
    H = []; W = [];
    Hf = []; Wf = [];
    for i = 1:numel(bb)
        if isempty(bb{i}), continue; end
        %     info = imfinfo(imfn{i});
        
        H = [H; bb{i}(:, 5)];
        W = [W; bb{i}(:, 4)];
        
        if any(2 > bb{i}(:, 5)) || any(2 > bb{i}(:, 4)) || any(200 < bb{i}(:, 5))
            imfn{i}
        end
        %     Hf = [Hf; bb{i}(:, 5) / info.Height];
        %     Wf = [Wf; bb{i}(:, 4) / info.Height];
    end
end
fig(1); clf;
% whitebg('black');
plot(H, W, 'r.', 'MarkerSize', 10);
grid on

sample_size = 30; % number of points to sample per trial
max_distance = 100; % max allowable distance for inliers

points = [H(:) W(:)];

fit_line_fcn = @(points) points(:, 1) \ points(:, 2); % fit function using polyfit
eval_line_fcn = ...   % distance evaluation function
    @(model, points) sum((points(:, 2) - points(:,1) * model).^2, 2);

[modelRANSAC, inliers] = ransac(points, fit_line_fcn, eval_line_fcn, ...
    sample_size, max_distance);
model_inliers = points(inliers, 1) \ points(inliers, 2)

hold on
inlier_pts = points(inliers, :);
x = [min(inlier_pts(:,1)) max(inlier_pts(:,1))];
y = model_inliers * x;
plot(x, y, 'g-')
plot(H(inliers), W(inliers), 'g.', 'MarkerSize', 15);
hold off
% fig(2); clf;
% plot(Hf, Wf, '.');
% grid on

% [B, ev, avg] = kspca([H W]');
