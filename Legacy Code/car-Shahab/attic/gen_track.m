rng('default'); rng(1);

X = generate_polygon(0, 0, 100, 0.3, 0.3, 20)';
X = [X X(:, 1)];
data = X';

w = 64;
h = 64;
gap = 8;


minX = min(data(:, 1));
maxX = max(data(:, 1));
minY = min(data(:, 2));
maxY = max(data(:, 2));

data(:, 1) = data(:, 1) - minX; maxX = maxX - minX; minX = 0;
data(:, 2) = data(:, 2) - minY; maxY = maxY - minY; minY = 0;

data(:, 1) = (w - 2 * gap) * data(:, 1) / maxX + gap;
data(:, 2) = (h - 2 * gap) * data(:, 2) / maxY + gap;







[xx, yy] = meshgrid(1:w, 1:h);

points = [xx(:) yy(:)];
[xy, d, t] = distance2curve(data, points, 'spline');
D = reshape(d, h, w);


scale = 2;
D = imresize(D, scale);
h = h * scale;
w = w * scale;
[xx, yy] = meshgrid(1:w, 1:h);

points = [xx(:) yy(:)];

figure(1); clf; 
sc(D > 2.5);

hold on
plot(data(:, 1) * scale, data(:, 2) * scale);
[a, b] = im2cones(D <= 2.5);
plot(a(2, :), a(1, :), 'b.');
plot(b(2, :), b(1, :), 'y.');
hold off
axis equal

k = 15;
[idxa, nnda] = knnsearch(a', points, 'K', k);
[idxb, nndb] = knnsearch(b', points, 'K', k);
X = [nnda nndb];

if 0
    sv = fitrsvm(X, D(:));
    pred = predict(sv, X);
end

layers = [imageInputLayer([1 size(X, 2) 1]);
          fullyConnectedLayer(100)
          reluLayer();
          fullyConnectedLayer(30);
          reluLayer();
            fullyConnectedLayer(1);
          regressionLayer()];
options = trainingOptions('sgdm','MaxEpochs',100,...
	'InitialLearnRate',0.00001);

x = X';
x = reshape(x, 1, [], 1, size(x, 2));
net = trainNetwork(x, (D(:) ), layers, options);
pred = predict(net, x);
figure(2); sc(reshape(pred, h, w));
hold on
plot(data(:, 1) * scale, data(:, 2) * scale);
[a, b] = im2cones(D <= 2.5);
plot(a(2, :), a(1, :), 'b.');
plot(b(2, :), b(1, :), 'y.');
hold off



