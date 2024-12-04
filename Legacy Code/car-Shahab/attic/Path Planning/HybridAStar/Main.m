vis = 1;
choose_start_end = 1;
vis_astar = 1;
vis_astar_search_space = 0;
vis_astar_collision = 0;
vis_astar_solution = 1;
vis_collision = 1;
smooth_path = 0;
load_track = 1;
fname = 'solution_collision'

global goal_node;
global start_node;
start_node = Node(82,90,1.34,0);
goal_node = Node(202,82,0,0);
global goal_r;
goal_r = Node.d;
%image resize
imscale = 1;

if load_track
    %loading track
    track = imread('complex_track.png');
    track = imresize(track, imscale);
    [h, w, z] = size(track);
    track = track(:,:,1);
    track = imbinarize(track);
    track = track==0;
else 
    %load cone positions
    fID = fopen('cone_pos', 'r');
    formatSpec = '%f %f';
    sizeA = [2 Inf];
    cone_pos = fscanf(fID, formatSpec, sizeA);
    cone_pos = cone_pos';
    scatter(cone_pos(:, 1), cone_pos(:,2));
end

%voronoi field
d = bwdist(track);
vf = mat2gray(d, [double(min(d(:))) double(max(d(:)))]);

%kd-tree
[x, y] = find(track);
obstacle_map = createns([y,x]);

%Grid(width, height) 
grd = Grid(w, h);

if vis
    figure('rend','painters','pos',[10 10 900 600])
    xlim([0 w]) 
    ylim([0 h])
    hold on
    grid on
    set(gca,'xtick',0:Node.cs:w)
    set(gca,'ytick',0:Node.cs:h)
    set(gca,'YTickLabel',[])
    set(gca,'XTickLabel',[])
    scatter(y, x,'.','k')
    %plotTrack(track)
    %track = mod(track+1, 2);
    %plotTrack(track);
    %scatter(find(track), '.');
    if choose_start_end
        [x,y] = ginput(2);
        start_node = Node(x(1),y(1),0,0);
        goal_node = Node(x(2),y(2),0,0);
    end
    plotCircle(goal_node.x, goal_node.y, goal_r, 'b');
    plotCircle(start_node.x, start_node.y, 0.1*Node.cs, 'b');
    pause(0.05);
end 

tic
path = hybrid_astar(grd, obstacle_map, vis_astar, vis_astar_search_space, vis_astar_collision);
toc
path

if logical(any(path(:)))
    if vis_astar_solution
        path_skeleton(path, vis_collision);
        %plot(path(1,:),path(2,:), "color", "red");
    end
    if smooth_path
        options = optimset('Display','iter');
        %smooth takes as input initial path, grid, 
        %voronoi field and maximum radius for a turn
        r = Node.vlen * tand(Node.amax);
        [cgpath, fval] = fminsearch(@(path) cg_smoothing(path, obstacle_map, vf, r), path, options);

        if vis
            plot(cgpath(1,:),cgpath(2,:), "color", "black");
        end
    end
end

export_fig(strcat('/home/teo/repos/cr/adr/img/', fname), '-png');

function path_skeleton(path, vis_collision)
    for i = 1:size(path,2)-1
        [x_coor, y_coor] = corner_points([path(1, i), path(2, i)], rad2deg(path(3, i)));  
        %pgon = polyshape(x_coor, y_coor);
        x_coor = [x_coor, x_coor(1)];
        y_coor = [y_coor, y_coor(1)];
        plot(x_coor, y_coor, 'Color', 'r');
        if vis_collision
            plotCircle(x_coor(1), y_coor(1), Node.ccr, 'k');
            plotCircle(x_coor(2), y_coor(2), Node.ccr, 'k');
            plotCircle(path(1, i), path(2, i), Node.cr, 'k');
        end
        %r = rectangle('Position', [path(1, i)-Node.vlen/2, path(2, i)-Node.vwidth/2, Node.vlen, Node.vwidth]);
    end
end

%plot track using black squares
function plotTrack(track)
    s = Node.cs;
    [h, w] = size(track)
    for i = (1:h)*Node.cs
        for j = (1:w)*Node.cs
            if track(i, j) == 1
                y = [i-s, i, i, i-s, i-s];
                x = [j-s, j-s, j, j, j-s];
                fill(x, y, 'k');
            end
        end
    end
end