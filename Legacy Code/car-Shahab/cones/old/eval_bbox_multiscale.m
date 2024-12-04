function [score, best_bbox] = eval_bbox_multiscale(cx, cy, h, im, buf, B, svm_vectors, svm_alphas, svm_bias, svm_scale)

best_score = -inf;
best_bbox = [];
for hh = h %linspace(31/32, 33/32, 3) * h%linspace(0.25 * h, 1.5 * h, 8)
    ww = cone_width_from_height(hh);
    xx = cx - (ww - 1) * 0.5;
    yy = cy - (hh - 1) * 0.5;
    score = eval_bbox(im, buf, B, svm_vectors, svm_alphas, svm_bias, svm_scale, ...
        [xx yy ww hh]);
    if score > best_score
        best_score = score;
        best_bbox = [xx yy ww hh];
    end
end
score = best_score;
