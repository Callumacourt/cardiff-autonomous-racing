data = csvread('id.csv');
% steering, throttle, ax, ay, az, wx, wy, wz, speed, theta

a = data(:, 10);
for i = 1:numel(a) - 1
    if a(i + 1) - a(i) < -3
        a(i + 1:end) = a(i + 1:end) + 2 * pi;
    end
        
    if a(i + 1) - a(i) > 3
        a(i + 1:end) = a(i + 1:end) - 2 * pi;
    end
end
data(:, 10) = a;

wz = data(:, 8);
idx = find(abs(wz) > 100);
for i = idx
    if abs(wz(i + 1)) < 100
        wz(i) = 0.5 * (wz(i - 1) + wz(i + 1));
    else
        wz(i) = 0.5 * (wz(i - 2) + wz(i + 2));
    end
end

%wz(idx) = 0;%0.5 * (wz(idx - 1) + wz(idx + 1));
data(:, 8) = wz;


ste = data(:, 1)';
thr = data(:, 2)';
ax = data(:, 3)';
ay = data(:, 4)';
wx = data(:, 6)';
wy = data(:, 7)';
wz = data(:, 8)';
speed = data(:, 9)';

%1234567
% 123456
%  12345
%
D = [ste; thr; ax; ay; wx; wy; wz; speed];
%D = [0 1 2 3 4 5 6 7 8 9; 10 11 12 13 14 15 16 17 18 19];
nh = 1;
H = zeros(size(D, 1) * nh, size(D, 2) - (nh - 1));
for i = 1:nh
    H(((nh - i + 1) - 1) * size(D, 1) + 1:(nh - i + 1) * size(D, 1), :) = D(:, i:i + size(H, 2) - 1);
end

forecast = 10;
X = H(:, 1:end-forecast);
Y = H(8, 1+forecast:end);
imdb = struct;
imdb.images = struct;
imdb.images.data = single(reshape(X, 1, 1, size(X, 1), size(X, 2)));
imdb.images.label = single(reshape(Y, 1, 1, size(Y, 1), size(Y, 2)));
imdb.images.set = ones(size(imdb.images.label));
imdb.images.set(1:10:end) = 2;

net = cnn_init_id(size(X, 1), size(Y, 1), 'bnorm', true);

epochs = 340;
trainOpts.batchSize = 1024; %size(X, 2);
trainOpts.gpus = 1;
trainOpts.learningRate = 0.000000256; %

design = [10, 5];
trainOpts.expDir = sprintf('cnn-id-%d-%d', ...
    design(1), design(2));

trainOpts.numEpochs = epochs;
trainOpts.continue = true;
[net,info] = cnn_train(net, imdb, @get_batch, trainOpts);

net = vl_simplenn_move(net, 'cpu') ;
net.layers(end) = [] ;
net = cnn_remove_bnorm(net);

res = vl_simplenn(net, imdb.images.data, [], [], 'ConserveMemory', true);
response = squeeze(res(end).x);

figure(2); clf;
plot(Y, response, '.')
figure(3); clf;
hold on
plot(Y(1000:1100));
plot(response(1000:1100));
hold off
