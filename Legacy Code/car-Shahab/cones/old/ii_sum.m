function I = ii_sum(J, y, x, h, w)

I = J(y + h, x + w) + J(y, x) - J(y, x + w) - J(y + h, x);