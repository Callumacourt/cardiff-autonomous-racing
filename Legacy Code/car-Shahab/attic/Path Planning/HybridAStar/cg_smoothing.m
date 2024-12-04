%path, voronoi field, 4 weights, maximum curvature, sigma O and sigma K
%penalty functions 
function res = cg_smoothing(path, om, vf, r)
    %[wp, wk] = deal(1);
    wp = 1;
    wo = 0.1;
    ws = 3;
    wk = 10;
    [tp, to, tk, ts] = deal(0);
    kmax = 1/r;
    persistent c;
    persistent h;
    for i = 1:size(path,2)
        x = path(1, i);
        y = path(2, i);
        [x_, y_] = discretize(x, y);
        [idx, o] = knnsearch(om, [x, y]);
        if i ~= size(path,2) && i ~= 1 
            tp = tp+vf(y_, x_);
            to = to+(abs(x-o) - Node.cr).^2;
            tk = tk+(deltaphi(path, i)/abs(deltav(path, i, 1) - kmax));
            ts = ts+(deltav(path, i+1, 1) - deltav(path, i, 1)).^2;
        else
            tp = tp+vf(y_,x_);
            to = to+(abs(x-o) - Node.cr).^2;
        end 
    end
    res = tp*wp + to*wo + tk*wk + ts*ws;
    if any(c == 1) || isempty(c)
        h = plot(path(1,:),path(2,:), "color", "black");
        c = 2;
    else
        h.XData = path(1,:);
        h.YData = path(2,:);
    end
    drawnow
end

function [cx, cy] = discretize(x, y)
    cx = ceil(x);
    cy = ceil(y);
end

%j is the choice of x y or theta, 1 2 and 3 respectively
function res = deltav(path, i, j)
    path = path(j:j, :);
    res = path(i) - path(i-1);
end

function res = deltaphi(path, i)
    res = abs(atan(deltav(path, i+1, 2)/deltav(path, i+1, 1)) - atan(deltav(path, i, 2)/deltav(path, i, 1)));
end

