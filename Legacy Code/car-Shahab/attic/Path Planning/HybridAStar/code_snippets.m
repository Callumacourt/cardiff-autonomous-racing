%threshhold for checking Dubins path
%{
dubinsc = max([(node.f-node.g).^2/25,1]);
if c >= dubinsc
    [path, len] = dubinspath(node, Node.vlen/tand(Node.amax), Node.d);
    c = 0;
    if vis
        plot(path(1,:),path(2,:), 'color', 'green');
    end
    if grd.collisionCheck(path)
        nodes_expanded
        pre = backtrace(node);
        res = [fliplr(pre(1:end,2:end)), path];
        size(pre,2)
        return
    end
end
c=c+1;
%}

%{
if logical(any(path(:)))
    if vis 
        skeleton(path);
        %plot(path(1,:),path(2,:), "color", "red");
    end
    
    options = optimset('Display','iter');
    %smooth takes as input initial path, grid, 
    %voronoi field and maximum radius for a turn
    r = Node.vlen * tand(Node.amax);
    vf = 1-vf;
    [cgpath, fval] = fminsearch(@(path) smooth(path, grd, vf, r), path, options);

    if vis
        cgpath
        plot(cgpath(1,:),cgpath(2,:), "color", "black");
    end
end
%}

function res = collisionCheck(obj, path)
    for i = 1:size(path, 2)
        x=path(1, i);
        y=path(2, i);
        if ~obj.isTraversable(x, y)
            res = 0;
            return
        end
    end
    res = 1;
end
