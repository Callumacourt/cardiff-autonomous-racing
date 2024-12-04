am = load('am_yb_vs_bg_26x21_90_c_rgb.mat');
% im = imread('../data/local/amz/000001.png');
% im = imread('/home/coriolan/research/cr/data/local/fs2019_track1_fixed/000001.png');
B = am.B .* repmat(am.a, size(am.B, 1), 1);
svm_vectors = am.svm_vectors - repmat(am.b', 1, size(am.svm_vectors, 2)) + repmat(B' * am.avg, 1, size(am.svm_vectors, 2));
svm_alphas = am.svm_alphas;
svm_bias = am.svm_bias;
svm_scale = single(1.0 / (am.svm_scale * am.svm_scale));

pitch = size(B, 1) / 3;
r = B(1:pitch, :);
g = B(pitch+1:pitch*2, :);
b = B(pitch*2+1:end, :);
Bcuda = zeros(size(B), 'like', B);
Bcuda(1:3:end, :) = r;
Bcuda(2:3:end, :) = g;
Bcuda(3:3:end, :) = b;


fn = list_files('/home/coriolan/research/car_data/cones/office.261019/*.jpg');

for i = 1:numel(fn)
% im = imread('/home/coriolan/research/cr/cones/fsuk 2019 recordings/track1/004585.jpg');
% im = im(:, 1:640, :);
%     im = cat(3, imadjust(medfilt2(im(:, :, 1), fs)), ...
%                 imadjust(medfilt2(im(:, :, 2), fs)), ...
%                 imadjust(medfilt2(im(:, :, 3), fs)));

% im = imadjust(im, [0 0 0; 1 1 1],[]);
% im = imread('/home/coriolan/research/cr/data/cones/silverstone18_kirill/IMG_20180714_133909.jpg');
% im = im(1:4:end, 1:4:end, :);
% im = im(1:480, 1:640, :);
im = imread(fn{i});


buf = zeros(am.ch, am.cw, size(im, 3), 'single');

if 0
    ww = am.cw; hh = am.ch;
    C = zeros(size(im, 1), size(im, 2));
    
    tic
    for cy = 1:size(im, 1)
        cy
        y = cy - (hh - 1) * 0.5;
        for cx = 1:size(im, 2)
            x = cx - (ww - 1) * 0.5;
            getwndnn(buf, im, x, y, ww, hh);
            proj = am_project_svm(buf(:), B, svm_vectors, svm_alphas, svm_bias, svm_scale);
            %         proj = am_project(buf(:), B);
            C(cy, cx) = proj;
        end
%         if mod(cy, 20) == 0
%             fig(2); sc(C);
%             drawnow;
%         end
    end
    toc
    fig(2); sc(C);
    
end

imopencv = matlab2opencv(im);

h0 = 32;
hh = linspace(8, 40, 5);
ww = 0.7902 * hh;
range = 4:4:32;
tw = 1;
th = 1;
% T = zeros(numel(range));
% for tw = 1:numel(range)
%     for th = 1:numel(range)
        
        iter = 1;
        t = tic;
%         for i = 1:iter
            x = am_project_svm_cuda(imopencv, Bcuda, svm_vectors, svm_alphas, svm_bias, svm_scale, ...
                range(tw), range(th), ww, hh);
%         end
        dt = toc(t);
%         T(tw, th) = 1000.0 * dt / iter;
%         T
        
        fprintf('%.2f ms\n', 1000 * dt / iter);
%     end
% end

figure(1);
% sc(imresize(x, 2))
sc(cat(1, sc(x), sc(im)));
drawnow;
end

% max(max(abs(C - x)))
