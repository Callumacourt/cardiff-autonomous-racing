opt.ch = 26;
opt.cw = 21;
opt.colour = true;
opt.labels = [0, 1];
opt.pad = [];
kernel_scale = 1.0;

if 0
    fprintf('Loading positive examples from annotations...');
    [Xpos, L, Xother, fn] = load_positive_patches(opt.labels, 'cw', opt.cw, 'ch', opt.ch, ...
        'colour', opt.colour, 'pad', opt.pad);
    fprintf('done\n');
end

if 0
    % Load negative patches
    fprintf('Loading negative examples...');
    Xneg = load('patches_26_21_neg_rgb_100000'); Xneg = Xneg.Xneg(:, 1:10:end);
    Xneg_mined = load('patches_26_21_neg_rgb_89179_mined'); Xneg_mined = Xneg_mined.Xneg(:, 1:1:end);
    Xneg = [Xneg Xother Xneg_mined];
    fprintf('done\n');
    % Resize if necessary
    if size(Xneg, 1) ~= opt.ch * opt.cw * 3
        Xneg = resize_patches(Xneg, opt.ch, opt.cw, opt.ch, opt.cw, opt.colour);
    end
end

% lab = [ones(1, size(Xpos, 2)) zeros(1, size(Xneg, 2))]';
% X = [Xpos Xneg]';
% % Noralise data to [0, 1]
if 0
    X_min = min(data, [], 2);
    X_max = max(data, [], 2);
    a = 1 ./ (X_max - X_min);
    b = -X_min .* a;
    data = double(bsxfun(@plus, bsxfun(@times, data, a), b) * 2 - 1);
    
    N0 = nnz(lab == 0);
    N1 = nnz(lab == 1);
    idx1 = find(lab == 1);
    Nextra = N0 - N1;
    idx = randi(numel(idx1), [1 Nextra]);
    data_extra = data(:, idx);
    data_b = [data data_extra];
    lab_b = [lab; ones(Nextra, 1)];
end

nh_range = [200:200:800 1000:400:4000];
c_range = 1;
RECALL = nan(numel(nh_range), numel(c_range));
E = nan(numel(nh_range), numel(c_range));
[X, Y] = meshgrid(c_range, nh_range);
for i = 1:numel(nh_range)
    for j = 1:numel(c_range)
        nh = nh_range(i);
        c = c_range(j);
                    CONF = zeros(2);

        for iter = 1:3
            tic
            [inW, bias, outW] = mexElmTrain(data_b(1:546, :), lab_b(:), nh, c);
            toc
            
            tic
            scores = mexElmPredict(inW, bias, outW, data(1:546, :));
            toc
            
            [~, pred] = max(scores);
            pred = 2 - pred;
            
            conf = confusion(lab(:), pred(:));
            CONF = CONF + conf;
        end
        [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(CONF);
        fprintf('recall: %.2f%%, spec: %.2f%%, prec: %.2f%%,\nF1: %.2f%%, acc: %.2f%%, bacc: %.2f%%\n', ...
            recall * 100, specificity * 100, precision * 100, ...
            F1 * 100, accuracy * 100, balanced_accuracy * 100);
        
        E(i, j) = (CONF(1, 2) + CONF(2, 1)) / sum(CONF(:));
        RECALL(i, j) = recall;
        
        fig(1);
        plot(nh_range, E);
        %         surf(X, Y, E);
        %         xlabel('C'); ylabel('\sigma');
        fig(3);
        plot(nh_range, RECALL);
        %         surf(X, Y, RECALL);
        %         xlabel('C'); ylabel('\sigma');
        
        drawnow;
        E
        RECALL
        
    end
end