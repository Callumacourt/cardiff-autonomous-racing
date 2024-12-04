load('stopSignsAndCars.mat');

bboxes = cell(size(gTruth.LabelData, 1), 1);
for i = 1:size(gTruth.LabelData, 1)
    bboxes{i} = [gTruth.LabelData.yellow{i}; gTruth.LabelData.blue{i}];        
end
%     bboxes{i} = [gTruth.LabelData.yellow{i}; gTruth.LabelData.blue{i}; gTruth.LabelData.solid{i}];        



fn = gTruth.DataSource.Source;

fprintf('Total examples: %d\n', sum(cellfun(@numel, bboxes) / 4));
empty = cellfun(@isempty, bboxes);
bboxes(empty) = [];
% fn = list_files('../data/amz/every100/0*.png');
fn = gTruth.DataSource.Source;
fn_test = fn(empty);
fn(empty) = [];


B = [];

for i = 1:numel(bboxes)
    B = [B; bboxes{i}];
end
w = round(mean(B(:, 3))) * 4;
h = round(mean(B(:, 4))) * 4;
IM = zeros(h, w, numel(fn));

count = 1;
for i = 1:numel(fn)
    im = rgb2gray(im2double(imread(fn{i})));
    for j = 1:size(bboxes{i}, 1)
        
    cone = im(bboxes{i}(j, 2):bboxes{i}(j, 2)+bboxes{i}(j, 4)-1, ...
        bboxes{i}(j, 1):bboxes{i}(j, 1)+bboxes{i}(j, 3)-1);
    IM(:, :, count) = imresize(cone, [h w]);
    count = count + 1;
    end
    
end
X = reshape(IM, h * w, []);
E = tsne_plot_images(X, IM);
imwrite(E(:, :, 1), 'tsne.png')