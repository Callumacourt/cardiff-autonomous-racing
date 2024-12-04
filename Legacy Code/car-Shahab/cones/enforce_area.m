function I = enforce_area(I, B)

% Enforce that the total area is preserved
Barea = B(3, :) * B(4, :)';
Iarea = I(3, :) * I(4, :)';
scale_area = Barea / Iarea;
I(3, :) = I(3, :) * sqrt(scale_area);
I(4, :) = I(4, :) * sqrt(scale_area);
