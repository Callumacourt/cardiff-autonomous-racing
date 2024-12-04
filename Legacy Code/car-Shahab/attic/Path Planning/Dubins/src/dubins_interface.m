
q0=[0,0,0]; 
q1=[5,5,0]; 

r=0.5
stepSize=0.0001
[path, len] = dubins(q0,q1,r,stepSize); 
hold on;
line([1, 2], [3, 4]);
line([2, 4], [4, 2]);
plot(path(1,:),path(2,:)); 
grid on;xlabel('x');ylabel('y');


%   dubins calculates an interpolated dubins cureve between two points q0 and
%   q1 with circles of radius r at the inputed stepSize.
%
%   q0 = [x1 (1x1), y1 (1x1), theta1 (1x1)];
%   q1 = [x2 (1x1), y2 (1x1), theta2 (1x1)];
%   r  = (1x1);
%   stepSize = (1x1);
%
%   path = [x;y;theta] (3xn) :  n is deteremined within the code but is a
%                               minimum of 1
%
%   The original code is from https://github.com/AndrewWalker/Dubins-Curves