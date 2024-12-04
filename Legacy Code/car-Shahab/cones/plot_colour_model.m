function plot_colour_model(models, gmm, colour_labels, varargin)

opt.space = 'hsv';
opt = parseargs(opt, varargin{:});

cp = models;

% gmm = fit_gmms(cp, [3 2]);
if 1
    skip = 1  ;
    whitebg('black');
    hold on
    for i = 1:numel(models)
        switch lower(opt.space)
            case 'hsv'
                x = rgb2hsv(cp{i}')';
            case 'rgb'
                x = cp{i};
        end
        plot3(x(1, 1:skip:end), x(2, 1:skip:end), x(3, 1:skip:end), '.', 'Color', colour_labels(i, :) / 255);
        plot_gmm(gmm{i}, colour_labels(i, :) / 255);
    end
        switch lower(opt.space)
            case 'hsv'
    xlabel('Hue'); ylabel('Saturation'); zlabel('Value');
            case 'rgb'
    xlabel('Red'); ylabel('Green'); zlabel('Blue');
        end    
    xlim([0 1]); ylim([0 1]); zlim([0 1]);
    
    grid on
    view(134, 57);
    
    hold off
end