function f = fig(n)

f = get(0, 'CurrentFigure');
if get(0, 'CurrentFigure') ~= n
    try
        set(0, 'CurrentFigure', n);
    catch
        f = figure(n);
    end
end
