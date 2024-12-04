
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
    
function [L_cones, R_cones] = trackimage2conepos(imscale, imname)
    im = imread(imname)
    
end