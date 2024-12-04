function mask = bbox_mask(h, w, bboxes)

mask = zeros(h, w);

for i = 1:size(bboxes, 1)
    mask(bboxes(i, 2):bboxes(i, 2) + bboxes(i, 4) - 1, ...
        bboxes(i, 1):bboxes(i, 1) + bboxes(i, 3) - 1) = 1;
end

