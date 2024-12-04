function gmm = fit_gmms(models, components, varargin)

opt.space = 'hsv';
opt = parseargs(opt, varargin{:});

gmm = cell(numel(models), 1);
for i = 1:numel(models)
    switch lower(opt.space)
        case 'hsv'
            gmm{i} = fitgmdist(rgb2hsv(models{i}'), components(i));
        case 'rgb'
            gmm{i} = fitgmdist(models{i}', components(i));
        otherwise
            error('Unknown colour model.');
    end
end