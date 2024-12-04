N = 10;

% bic = [];
% aic = [];
% for i = 1:20
%     i

options = statset('Display', 'final', 'MaxIter', 1000);
gmm = fitgmdist(proj, N, 'Replicates', 10, 'CovarianceType', 'diagonal', ...
    'SharedCovariance', false, ...
    'Options', options);
% bic(end + 1) = gmm.BIC;
% aic(end + 1) = gmm.AIC;
% end
