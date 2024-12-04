function I = enforce_cm(I, B)

% Enforce that the total centre of mass is preserved
Bcx = mean(B(1, :) + (B(3, :) - 1) * 0.5);
Bcy = mean(B(2, :) + (B(4, :) - 1) * 0.5);
Icx = mean(I(1, :) + (I(3, :) - 1) * 0.5);
Icy = mean(I(2, :) + (I(4, :) - 1) * 0.5);
I(1, :) = I(1, :) - (Icx - Bcx);
I(2, :) = I(2, :) - (Icy - Bcy);
