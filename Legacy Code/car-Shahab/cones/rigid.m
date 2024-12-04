function X = rigid(H, X)

X = unhomo_slow(H * homo_slow(X));