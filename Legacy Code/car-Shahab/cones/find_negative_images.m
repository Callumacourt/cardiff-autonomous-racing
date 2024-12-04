function negfn = find_negative_images()

%     negfn_all = [list_files('../data/negative/all/*.jpg'); ...
%         list_files('../data/negative/all/*.png')];
negfn_all = [glob('../../car_data/negative/**.jpg'); ...
    glob('../../car_data/negative/**.jpeg');
    glob('../../car_data/negative/**.png')];
fprintf('Found %d negative images.\n', numel(negfn_all));
negfn = {};
warning('off')
for i = 1:numel(negfn_all)
    info = imfinfo(negfn_all{i});
    if info.BitDepth ~= 24, continue; end
    negfn{end + 1} = negfn_all{i};
end
warning('on')
% negfn = negfn_all;

Nnegim = numel(negfn);
fprintf('Of them %d are in colour.\n', Nnegim);
