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
wz(idx) = 0;%0.5 * (wz(idx - 1) + wz(idx + 1));
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
Y = H(7, 1+forecast:end);

% [idx_train, idx_val, idx_test] = dividerand(size(X, 2), 80, 0, 20);
% 
% net = feedforwardnet([5 5]);
% % net.inputs{1}.processFcns = {};
% net = configure(net, X, Y);
% % net.layers{1}.transferFcn = 'poslin';
% % net.layers{2}.transferFcn = 'poslin';
% % net.layers{3}.transferFcn = 'poslin';
% net.divideFcn = 'dividerand';
% % net.divideFcn = 'divideind';
% % net.divideParam.trainInd = find(idx_train);
% % net.divideParam.valInd	 = find(idx_val);
% % net.divideParam.testInd  = find(idx_test);
% net.trainParam.showCommandLine = true;
% net.trainParam.max_fail = 10000;
% net.trainParam.epochs = 3000;
% 
% net = train(net, X, Y, 'useGPU', 'yes');


pred = sim(net, X(:, idx_train));
d = sum((Y(:, idx_train) - pred) .^ 2, 1);
sqrt(mean(d(:)))

pred = sim(net, X(:, idx_test));
d = sum((Y(:, idx_test) - pred) .^ 2, 1);
sqrt(mean(d(:)))


pred_net = sim(net, X);
figure(1); clf;
hold on
plot(Y(1:1000));
plot(pred_net(1:1000));
hold off
