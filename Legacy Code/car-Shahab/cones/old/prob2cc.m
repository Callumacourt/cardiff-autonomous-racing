function [cc, C] = prob2cc(P, t)

stdP = std(P(:));
meanP = mean(P(:));
C = (P > meanP + 2 * stdP) & t;
% meanP + 2 * stdP



% c = deleteoutliers(P(:), 0.05, 1);

cc = bwconncomp(C);