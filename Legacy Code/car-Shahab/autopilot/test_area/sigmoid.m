function x = sigmoid(x)

x = 2 ./ (1 + exp(-x * 2)) - 1;
