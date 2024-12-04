function a = accumulate_angle(a)
for i = 1:numel(a) - 1
    if a(i + 1) - a(i) < -3
        a(i + 1:end) = a(i + 1:end) + 2 * pi;
    end
        
    if a(i + 1) - a(i) > 3
        a(i + 1:end) = a(i + 1:end) - 2 * pi;
    end
end
