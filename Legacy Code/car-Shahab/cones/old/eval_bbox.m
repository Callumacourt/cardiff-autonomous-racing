function score = eval_bbox(im, buf, B, svm_vectors, svm_alphas, svm_bias, svm_scale, b)

% ch = am.ch; cw = am.cw;
% buf = zeros([ch cw size(im, 3)], 'single');
getwndbl_scale(buf, im, b(1), b(2), b(3), b(4));

% fig(1); sc(buf); drawnow;
% 
% buf = buf(:);
% buf = buf(am.mask);

score = am_project_svm(buf(:), B, svm_vectors, svm_alphas, svm_bias, svm_scale);


% proj = am.B' * subcol(buf(:), am.avg);
% rec = addcol(am.B * proj, am.avg);
% rec = reshape(rec, am.ch, am.cw, size(im, 3));
% 
% score = -mean(abs(rec(:) - buf(:)));


