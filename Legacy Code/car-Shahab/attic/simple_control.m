theta = deg2rad(1); % speed car changes direction
speed = 2;
n = 1000; % no. of iterations simulated

% load cones (L - left/R - right)
L = [575,600,0;
    430,620,0;
    275,610,0;
    220,490,0;
    330,418,0;
    385,354,0;
    310,290,0;
    150,180,0;
    40,5,0];
R = [565,481,0;
    460,490,0;
    360,520,0;
    510,380,0;
    480,230,0;
    340,160,0;
    230,70,0;
    170,10,0];

% load track (cone graph)
% g = [s1,t1;s2,t2;...]
L_g = [1,2;2,3;3,4;4,5;5,6;6,7;7,8;8,9];
R_g = [1,2;2,3;3,4;4,5;5,6;6,7;7,8];

% init car
C_t = [100,0,0]; % position
C_r = [0,1,0]; % direction facing (unit vector)

figure;
for iter=1:n
    % visualise cones/track & car
    clf;
    hold on;
    % show cones
    scatter3(L(:,1),L(:,2),L(:,3),[500],'.','MarkerEdgeColor',[.5 1 0]);
    scatter3(R(:,1),R(:,2),R(:,3),[500],'.','MarkerEdgeColor',[0 .5 1]);
    % show track
    for i=1:length(L_g)
        temp = [L(L_g(i,1),:);L(L_g(i,2),:)];
        plot3(temp(:,1),temp(:,2),temp(:,3),'Color',[.5 1 0]);
    end
    for i=1:length(R_g)
        temp = [R(R_g(i,1),:);R(R_g(i,2),:)];
        plot3(temp(:,1),temp(:,2),temp(:,3),'Color',[0 .5 1]);
    end
    % show car
    scatter3(C_t(1),C_t(2),C_t(3));
    temp = [C_t;C_t+(C_r .* 25)];
    plot3(temp(:,1),temp(:,2),temp(:,3),'Color',[0 .5 1]);
    axis equal;
    hold off;

    % ---- Left cones ----
    % Find the 2 nearest cones on the left side of the car
    kd = KDTreeSearcher(L);
    idz = knnsearch(kd,C_t,'K',2);

    a = L(idz(1),:) - L(idz(2),:); % vector between the 2 cones next to the car
    u = [0,-a(3),a(2)];
    n = cross(u,a); % vector orthogonal to cones
    n = n / norm(n); % normal unit vector

    hold on; % visualise normal
    temp = [L(idz(1),:);L(idz(1),:)+(n .* 25)];
    plot3(temp(:,1),temp(:,2),temp(:,3),'Color',[0 .5 1]);
    hold off;

    v = C_t - L(idz(1),:); % vector between the car and the first cone
    dist = dot(v,n); % project the car vector orthogonally onto the cone vector
    LP_t = C_t - dist*n; % position of projected point
    L_wall_dist = norm(C_t-LP_t); % distance between plane between the 2 cone and the car
    hold on; scatter3(LP_t(1),LP_t(2),LP_t(3)); hold off; % visualise projected point

    % ---- Right cones ----
    % Find the 2 nearest cones on the right side of the car
    kd = KDTreeSearcher(R);
    idz = knnsearch(kd,C_t,'K',2);

    a = R(idz(1),:) - R(idz(2),:); % vector between the 2 cones next to the car
    u = [0,-a(3),a(2)];
    n = cross(u,a); % vector orthogonal to cones
    n = n / norm(n); % normal unit vector

    hold on; % visualise normal
    temp = [R(idz(1),:);R(idz(1),:)+(n .* 25)];
    plot3(temp(:,1),temp(:,2),temp(:,3),'Color',[0 .5 1]);
    hold off;

    v = C_t - R(idz(1),:); % vector between the car and the first cone
    dist = dot(v,n); % project the car vector orthogonally onto the cone vector
    RP_t = C_t - dist*n; % position of projected point
    R_wall_dist = norm(C_t-RP_t); % distance between plane between the 2 cone and the car
    hold on; scatter3(RP_t(1),RP_t(2),RP_t(3)); hold off; % visualise projected point

    if L_wall_dist < R_wall_dist % turn left
        angle = theta;
    else % turn right
        angle = -theta;
    end
    
    C_r = C_r * [cos(angle),-sin(angle),0;sin(angle),cos(angle),0;0,0,1]; % update car direction
    C_t = C_t + (speed * C_r); % update car postition
    drawnow;
end