function [best_score, bboxf] = refine_bbox_grid(im, am, svm_vectors, svm_alphas, svm_bias, b)

buf = zeros([am.ch, am.cw, size(im, 3)], 'single');


[h, w] = force_cone_dimensions(b(4), b(3));
xnew = b(1) + (b(3) - w) * 0.5;
ynew = b(2) + (b(4) - h) * 0.5;


bbox = [xnew ynew w h];
c = bbox_centroids(bbox);

x = c(1); y = c(2);


step_x = 0.25 * w;
step_y = 0.25 * h;

for iter = 1:10
    best_score = -inf;
    best_dx = [];
    best_dy = [];
    best_bbox = [];
    for dx = [-step_x 0 step_x]
        for dy = [-step_y 0 step_y]
            [score, b] = eval_bbox_multiscale(x + dx, y + dy, h, ...
                im, buf, am, svm_vectors, svm_alphas, svm_bias);
            if score > best_score
                best_score = score;
                best_dx = dx;
                best_dy = dy;
                best_bbox = b;
            end
        end
    end
    
    step_x = 0.5 * step_x;
    step_y = 0.5 * step_y;
    if step_x < 0.5 || step_y < 0.5, break; end
    x = x + best_dx;
    y = y + best_dy;
end

bboxf = best_bbox;


