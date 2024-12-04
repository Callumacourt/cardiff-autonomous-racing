opt.negative_folder = '../data/negative/all';
opt.labels = [0, 1];
opt.scale = 1.25;
opt.features = 'haar';
opt.far = 0.5;
opt.tpr = 0.999;
opt.nsf = 2;
opt.stages = 25;
opt.wh = 12;
opt.ww = round(cone_width_from_height(opt.wh));

data = prepare_for_cascade_training('labels', opt.labels, 'scale', opt.scale);

% Devise the detector filename
label_names = 'ybsr';

det_fn = sprintf('cone_detector_%s_%s_pad%.0f_%02dx%02d_st%d_far%.3f_tpr%.3f_nsf%.1f.xml', ...
    opt.features, label_names(opt.labels + 1), opt.scale * 100, opt.wh, opt.ww, ...
    opt.stages, opt.far, opt.tpr, opt.nsf);

% Train cascade detector
trainCascadeObjectDetector(det_fn, data, opt.negative_folder, ...
    'ObjectTrainingSize', [opt.wh opt.ww] , ...
    'FalseAlarmRate', opt.far, ...
    'TruePositiveRate', opt.tpr, ...
    'NumCascadeStages', opt.stages, ...
    'FeatureType', opt.features, ...
    'NegativeSamplesFactor', opt.nsf);
