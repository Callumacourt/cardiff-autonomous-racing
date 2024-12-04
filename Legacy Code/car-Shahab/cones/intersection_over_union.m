function iou = intersection_over_union(h, w, a, b)

A = bbox_mask(h, w, a);
B = bbox_mask(h, w, b);
iou = nnz(A & B) / nnz(A | B);
if isnan(iou), iou = 0; end
