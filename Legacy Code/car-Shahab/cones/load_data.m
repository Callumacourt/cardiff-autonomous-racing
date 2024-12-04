function [fn, P, gmm, models, template, labels, colour_labels] = load_data(name, varargin)

opt.tables = true;
opt.space = 'hsv';
opt = parseargs(opt, varargin{:});

fprintf('Experiment: %s\n', name);
path = ['../data/' name];

fprintf('Listing files...\n');
fn = list_files(fullfile(path, '*.png'));

fprintf('Loading template...\n');
try
template = imread(fullfile(path, 'template.png'));
template = logical(template(:, :, 1));
catch
    im = imread(fn{1});
    [h, w, d] = size(im);
    template = true(h, w);
end
fprintf('Loading colour models...\n');
switch lower(name)
    case 'fsuk17_cropped'
        template(1:500, :) = 0; % Blank out the sky as well
        
        labels = {'green', 'yellow', 'blue', 'red', 'asphalt'};
        colour_labels = [0 255 0; 255 255 0; 0 0 255; 255 0 0; 128 128 128];
        
        cp_green = load_colour_model('models/fsuk17_cone_green.txt');
        cp_yellow = load_colour_model('models/fsuk17_cone_yellow.txt');
        cp_blue = load_colour_model('models/fsuk17_cone_blue.txt');
        cp_red = load_colour_model('models/fsuk17_cone_red.txt');
        cp_asphalt = load_colour_model('models/fsuk17_asphalt.txt');
        
        models = {cp_green, cp_yellow, cp_blue, cp_red, cp_asphalt};
        fprintf('Fitting Gaussian mixture models...\n');
        gmm = fit_gmms(models, [1 2 1 2 4], 'space', opt.space);
    case 'amz'
        labels = {'yellow', 'blue', 'asphalt'};
        colour_labels = [255 255 0; 100 100 100; 0 0 255; 255 255 255; 128 128 128];
        
        cp_yellow = load_colour_model('models/amz_cone_yellow.txt');
        cp_black = load_colour_model('models/amz_cone_black.txt');
        cp_blue = load_colour_model('models/amz_cone_blue.txt');
        cp_white = load_colour_model('models/amz_cone_white.txt');
        cp_asphalt = load_colour_model('models/amz_asphalt.txt');
        
        models = {cp_yellow, cp_asphalt, cp_blue, cp_white, cp_black};
        fprintf('Fitting Gaussian mixture models...\n');
        switch lower(opt.space)
            case 'hsv'
                gmm = fit_gmms(models, [4 2 3 2 2], 'space', opt.space);
            case 'rgb'
                gmm = fit_gmms(models, [2 1 2 1 1], 'space', opt.space);
        end
        
        %         template = true(size(template));
            case 'single_lap'
        labels = {'yellow', 'blue', 'asphalt'};
        colour_labels = [255 255 0; 100 100 100; 0 0 255; 255 255 255; 128 128 128];
        
        cp_yellow = load_colour_model('models/single_lap_cone_yellow.txt');
        cp_black = load_colour_model('models/amz_cone_black.txt');
        cp_blue = load_colour_model('models/single_lap_cone_blue.txt');
        cp_white = load_colour_model('models/amz_cone_white.txt');
        cp_asphalt = load_colour_model('models/amz_asphalt.txt');
        
        models = {cp_yellow, cp_asphalt, cp_blue, cp_white, cp_black};
        fprintf('Fitting Gaussian mixture models...\n');
        switch lower(opt.space)
            case 'hsv'
                gmm = fit_gmms(models, [3 3 3 2 2], 'space', opt.space);
            case 'rgb'
                gmm = fit_gmms(models, [2 1 2 1 1], 'space', opt.space);
        end
        
        %         template = true(size(template));
    otherwise
        error('No such experiment.');
end


if opt.tables
    fprintf('Computing look-up tables...\n');
    P = compute_lookup_tables(gmm, 'space', opt.space);
else
    P = [];
    fprintf('NOT computing look-up tables.\n');
end

