function [score] = eval_bbox_multiscale_cnn(cx, cy, h, im, buf, net)

best_score = -inf(3, 1);

% best_bbox = [];
for hh = h %linspace(31/32, 33/32, 3) * h%linspace(0.25 * h, 1.5 * h, 8)
    ww = cone_width_from_height(hh);
    xx = cx - (ww - 1) * 0.5;
    yy = cy - (hh - 1) * 0.5;
    getwndbl_scale(buf, im, xx, yy, ww, hh);
    buf_gpu = gpuArray(buf);
    tic
    res = vl_simplenn(net, buf_gpu, [], [], 'ConserveMemory', true);
    toc
    score = softmax(squeeze(gather(res(end).x)));
    best_score = max(best_score, score);
%     if score > best_score
%         best_score = score;
%         best_bbox = [xx yy ww hh];
%     end
end
score = best_score;
