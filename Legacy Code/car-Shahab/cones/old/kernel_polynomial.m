function G = kernel_polynomial(A, B)

G = (A * B') .^ 2;
